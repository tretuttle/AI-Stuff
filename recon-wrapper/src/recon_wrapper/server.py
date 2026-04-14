"""HTTP + SSE server. Stdlib only.

Routing is explicit and compact. Every endpoint is either:
  - GET returning JSON
  - GET returning SSE (text/event-stream)
  - POST accepting JSON body
  - DELETE returning 204

Auth: Authorization: Bearer <token>. Token auto-generated at ~/.claude/recon/token.
"""
from __future__ import annotations
import json
import re
import queue
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from . import aggregator, models as m
from . import API_VERSION, DATA_VERSION, __version__
from .actions import JobRegistry
from .config import Config, ensure_token
from .watcher import FileWatcher


# ------- route table -------

Handler = Callable[["Context"], None]


class Context:
    def __init__(self, handler: "ReconHTTPHandler", match: re.Match | None):
        self.h = handler
        self.m = match

    def param(self, name: str) -> str:
        assert self.m is not None
        return urllib.parse.unquote(self.m.group(name))

    def query(self) -> dict[str, str]:
        q = self.h.path.split("?", 1)
        if len(q) == 1:
            return {}
        return {k: v[0] for k, v in urllib.parse.parse_qs(q[1]).items()}

    def body_json(self) -> dict:
        length = int(self.h.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.h.rfile.read(length)
        return json.loads(raw.decode("utf-8"))


def _routes() -> list[tuple[str, str, Handler]]:
    return [
        ("GET",    r"^/health$",                         h_health),
        ("GET",    r"^/schema$",                         h_schema),
        ("GET",    r"^/projects$",                       h_projects),
        ("GET",    r"^/projects/(?P<slug>[^/]+)$",       h_project),
        ("GET",    r"^/projects/(?P<slug>[^/]+)/context$", h_project_context),
        ("GET",    r"^/graph$",                          h_graph),
        ("GET",    r"^/actions/(?P<id>[^/]+)/stream$",   h_action_stream),
        ("GET",    r"^/actions/(?P<id>[^/]+)$",          h_action_get),
        ("DELETE", r"^/actions/(?P<id>[^/]+)$",          h_action_cancel),
        ("POST",   r"^/actions$",                        h_action_submit),
        ("GET",    r"^/events$",                         h_events),
    ]


# ------- handlers -------

def h_health(c: Context) -> None:
    import shutil, subprocess
    cfg = c.h.server.cfg
    bin_path = shutil.which(cfg.claude_bin)
    version = None
    if bin_path:
        try:
            v = subprocess.run([bin_path, "--version"], capture_output=True, timeout=2, text=True)
            version = (v.stdout or v.stderr).strip()[:128]
        except Exception:
            pass
    projects = aggregator.list_projects(cfg)
    payload: m.Health = {
        "ok": True,
        "claude_bin": cfg.claude_bin,
        "claude_available": bin_path is not None,
        "data_root": str(cfg.claude_dir),
        "projects_tracked": len(projects),
    }
    if version:
        payload["claude_version"] = version
    _json(c.h, payload)


def h_schema(c: Context) -> None:
    payload: m.SchemaInfo = {"api": API_VERSION, "data": DATA_VERSION, "server_version": __version__}
    _json(c.h, payload)


def h_projects(c: Context) -> None:
    q = c.query()
    status = q.get("status")
    rows = aggregator.list_projects(c.h.server.cfg)
    if status:
        rows = [r for r in rows if r["status"] == status]
    _json(c.h, rows)


def h_project(c: Context) -> None:
    slug = c.param("slug")
    detail = aggregator.get_project(c.h.server.cfg, slug)
    if detail is None:
        _json(c.h, {"error": "not_found", "slug": slug}, status=404)
        return
    _json(c.h, detail)


def h_project_context(c: Context) -> None:
    slug = c.param("slug")
    detail = aggregator.get_project(c.h.server.cfg, slug)
    if detail is None:
        _json(c.h, {"error": "not_found", "slug": slug}, status=404)
        return
    _json(c.h, detail["context_files"])


def h_graph(c: Context) -> None:
    _json(c.h, aggregator.build_graph(c.h.server.cfg))


def h_action_submit(c: Context) -> None:
    try:
        body = c.body_json()
        req: m.ActionRequest = {  # type: ignore[typeddict-item]
            "kind": body["kind"],
            "cwd": body["cwd"],
        }
        for k in ("prompt", "resume_session", "output_format"):
            if k in body:
                req[k] = body[k]  # type: ignore[typeddict-unknown-key]
        job = c.h.server.jobs.submit(req)
        _json(c.h, job.snapshot(), status=202)
    except (KeyError, ValueError) as e:
        _json(c.h, {"error": "bad_request", "detail": str(e)}, status=400)


def h_action_get(c: Context) -> None:
    job = c.h.server.jobs.get(c.param("id"))
    if not job:
        _json(c.h, {"error": "not_found"}, status=404)
        return
    _json(c.h, job.snapshot())


def h_action_cancel(c: Context) -> None:
    ok = c.h.server.jobs.cancel(c.param("id"))
    if not ok:
        _json(c.h, {"error": "cannot_cancel"}, status=409)
        return
    c.h.send_response(204); c.h.end_headers()


def h_action_stream(c: Context) -> None:
    job = c.h.server.jobs.get(c.param("id"))
    if not job:
        _json(c.h, {"error": "not_found"}, status=404)
        return
    q = job.subscribe()
    try:
        _sse_start(c.h)
        while True:
            try:
                event, data = q.get(timeout=15)
            except queue.Empty:
                _sse_write(c.h, "ping", "")
                if job.state in ("completed", "failed", "canceled"):
                    break
                continue
            _sse_write(c.h, event, data)
            if event in ("completed", "failed", "canceled"):
                break
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        job.unsubscribe(q)


def h_events(c: Context) -> None:
    q = c.h.server.event_bus.subscribe()
    try:
        _sse_start(c.h)
        while True:
            try:
                event, data = q.get(timeout=15)
                _sse_write(c.h, event, data)
            except queue.Empty:
                _sse_write(c.h, "ping", "")
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        c.h.server.event_bus.unsubscribe(q)


# ------- response helpers -------

def _json(h: "ReconHTTPHandler", payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")
    h.send_response(status)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(body)))
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Headers", "authorization, content-type")
    h.end_headers()
    h.wfile.write(body)


def _sse_start(h: "ReconHTTPHandler") -> None:
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-cache")
    h.send_header("Access-Control-Allow-Origin", "*")
    h.end_headers()


def _sse_write(h: "ReconHTTPHandler", event: str, data: str) -> None:
    payload = f"event: {event}\ndata: {data}\n\n"
    h.wfile.write(payload.encode("utf-8"))
    h.wfile.flush()


# ------- event bus (for /events) -------

class EventBus:
    def __init__(self) -> None:
        self._subs: list[queue.Queue] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subs.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subs:
                self._subs.remove(q)

    def publish(self, payload: dict) -> None:
        event = payload.get("type", "message")
        data = json.dumps(payload, default=str, separators=(",", ":"))
        with self._lock:
            for q in list(self._subs):
                q.put((event, data))


# ------- request handler -------

class ReconHTTPHandler(BaseHTTPRequestHandler):
    server: "ReconServer"  # type: ignore[assignment]

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "authorization, content-type")
        self.end_headers()

    def _dispatch(self, method: str) -> None:
        if not self._auth_ok():
            _json(self, {"error": "unauthorized"}, status=401)
            return
        path = self.path.split("?", 1)[0]
        for (m_, pattern, handler) in _routes():
            if m_ != method:
                continue
            match = re.match(pattern, path)
            if match:
                try:
                    handler(Context(self, match))
                except Exception as e:
                    _json(self, {"error": "server_error", "detail": str(e)}, status=500)
                return
        _json(self, {"error": "not_found", "path": path}, status=404)

    def do_GET(self) -> None: self._dispatch("GET")
    def do_POST(self) -> None: self._dispatch("POST")
    def do_DELETE(self) -> None: self._dispatch("DELETE")

    def log_message(self, format: str, *args) -> None:
        # Quiet stderr; write to log file instead
        with open(self.server.cfg.log_file, "a") as fh:
            fh.write("[%s] %s\n" % (self.log_date_time_string(), format % args))

    def _auth_ok(self) -> bool:
        if self.path.startswith("/health") or self.path.startswith("/schema"):
            return True  # unauthenticated probes
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        return auth.split(" ", 1)[1].strip() == self.server.token


class ReconServer(ThreadingHTTPServer):
    def __init__(self, cfg: Config):
        super().__init__((cfg.host, cfg.port), ReconHTTPHandler)
        self.cfg = cfg
        self.token = ensure_token(cfg)
        self.jobs = JobRegistry(cfg)
        self.event_bus = EventBus()
        self.watcher = FileWatcher(cfg, self.event_bus.publish)


def serve(cfg: Config | None = None) -> None:
    cfg = cfg or Config.from_env()
    cfg.recon_dir.mkdir(parents=True, exist_ok=True)
    srv = ReconServer(cfg)
    srv.watcher.start()
    print(f"recon-wrapper v{__version__} on http://{cfg.host}:{cfg.port}")
    print(f"token: {srv.token}")
    print(f"token file: {cfg.token_file}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.watcher.stop()
        srv.shutdown()
