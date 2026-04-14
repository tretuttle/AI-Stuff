"""Spawn `claude -p` headlessly in a target cwd. Track jobs in-process.

Actions are fire-and-track:
  1. POST /actions returns an id immediately
  2. Worker thread streams stdout/stderr into a queue
  3. GET /actions/{id}/stream (SSE) yields lines as they arrive
  4. GET /actions/{id} returns current state
  5. DELETE /actions/{id} terminates the subprocess

All state is in-memory; restarting the wrapper clears the job table.
"""
from __future__ import annotations
import subprocess
import threading
import queue
import uuid
import time
import os
import pathlib
from dataclasses import dataclass, field
from typing import Optional

from .config import Config
from . import models as m


# Maps action kind → argv transformation.
# "prompt" is the escape hatch for anything the skills don't already cover.
_KIND_PROMPTS = {
    "recon": "/project-recon:recon",
    "conversation-recon": "/project-recon:conversation-recon",
}


@dataclass
class Job:
    id: str
    kind: str
    cwd: str
    state: str = "pending"  # pending | running | completed | failed | canceled
    started_at: str = ""
    ended_at: Optional[str] = None
    exit_code: Optional[int] = None
    _proc: Optional[subprocess.Popen] = None
    _events: "queue.Queue[tuple[str, str]]" = field(default_factory=queue.Queue)
    _stdout_bytes: int = 0
    _stderr_bytes: int = 0
    artifacts: list[str] = field(default_factory=list)
    _subscribers: list["queue.Queue[tuple[str, str]]"] = field(default_factory=list)
    _history: list[tuple[str, str]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def snapshot(self) -> m.ActionState:
        return {
            "id": self.id,
            "kind": self.kind,
            "cwd": self.cwd,
            "status": self.state,  # type: ignore[typeddict-item]
            "started_at": self.started_at,
            "exit_code": self.exit_code if self.exit_code is not None else 0,
            "stdout_bytes": self._stdout_bytes,
            "stderr_bytes": self._stderr_bytes,
            "artifacts": list(self.artifacts),
            **({"ended_at": self.ended_at} if self.ended_at else {}),
        }

    def emit(self, event: str, data: str) -> None:
        with self._lock:
            self._history.append((event, data))
            for sub in list(self._subscribers):
                sub.put((event, data))

    def subscribe(self) -> "queue.Queue[tuple[str, str]]":
        q: "queue.Queue[tuple[str, str]]" = queue.Queue()
        with self._lock:
            for ev in self._history:
                q.put(ev)
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: "queue.Queue[tuple[str, str]]") -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)


class JobRegistry:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, req: m.ActionRequest) -> Job:
        cwd = req["cwd"]
        if not pathlib.Path(cwd).is_dir():
            raise ValueError(f"cwd does not exist: {cwd}")

        kind = req["kind"]
        if kind == "prompt":
            prompt = req.get("prompt") or ""
            if not prompt.strip():
                raise ValueError("kind=prompt requires non-empty prompt")
        elif kind in _KIND_PROMPTS:
            prompt = _KIND_PROMPTS[kind]
        else:
            raise ValueError(f"unknown kind: {kind}")

        fmt = req.get("output_format") or "stream-json"
        resume = req.get("resume_session")

        argv = [self.cfg.claude_bin, "-p", prompt, "--output-format", fmt]
        if resume:
            argv += ["--resume", resume]

        job = Job(
            id=uuid.uuid4().hex[:12],
            kind=kind,
            cwd=cwd,
            started_at=_now_iso(),
        )
        with self._lock:
            self.jobs[job.id] = job
        threading.Thread(target=self._run, args=(job, argv), daemon=True).start()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self.jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job or not job._proc:
            return False
        try:
            job._proc.terminate()
            job.state = "canceled"
            job.ended_at = _now_iso()
            job.emit("canceled", "")
            return True
        except Exception:
            return False

    def _run(self, job: Job, argv: list[str]) -> None:
        try:
            job.state = "running"
            job.emit("started", "")
            proc = subprocess.Popen(
                argv,
                cwd=job.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy(),
                bufsize=1,
                text=True,
            )
            job._proc = proc

            t_out = threading.Thread(target=self._pump, args=(job, proc.stdout, "stdout"), daemon=True)
            t_err = threading.Thread(target=self._pump, args=(job, proc.stderr, "stderr"), daemon=True)
            t_out.start(); t_err.start()

            rc = proc.wait()
            t_out.join(timeout=2); t_err.join(timeout=2)
            job.exit_code = rc
            job.ended_at = _now_iso()
            job.state = "completed" if rc == 0 else "failed"
            job.emit("completed" if rc == 0 else "failed", str(rc))
        except FileNotFoundError:
            job.state = "failed"
            job.ended_at = _now_iso()
            job.exit_code = 127
            job.emit("failed", f"claude binary not found: {self.cfg.claude_bin}")
        except Exception as e:
            job.state = "failed"
            job.ended_at = _now_iso()
            job.emit("failed", str(e))

    def _pump(self, job: Job, stream, tag: str) -> None:
        if stream is None:
            return
        try:
            for line in iter(stream.readline, ""):
                if not line:
                    break
                if tag == "stdout":
                    job._stdout_bytes += len(line)
                else:
                    job._stderr_bytes += len(line)
                job.emit(tag, line.rstrip("\n"))
        finally:
            try:
                stream.close()
            except Exception:
                pass


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
