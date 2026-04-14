"""Watch ~/.claude/projects/** for new jsonl files. Emit events over SSE.

Polling fallback (stdlib). If `watchdog` is installed, prefer it.
"""
from __future__ import annotations
import os
import pathlib
import threading
import time
import queue
from typing import Callable

from .config import Config


class FileWatcher:
    """Tracks jsonl file mtimes per slug; emits events when a file appears or grows."""

    def __init__(self, cfg: Config, emit: Callable[[dict], None], poll_interval: float = 2.0):
        self.cfg = cfg
        self.emit = emit
        self.poll_interval = poll_interval
        self._state: dict[str, float] = {}  # path → mtime
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._prime()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _dirs(self) -> list[pathlib.Path]:
        dirs = [self.cfg.projects_dir]
        if self.cfg.windows_projects_dir.is_dir():
            dirs.append(self.cfg.windows_projects_dir)
        return [d for d in dirs if d.is_dir()]

    def _scan(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for base in self._dirs():
            for slug_dir in base.iterdir():
                if not slug_dir.is_dir():
                    continue
                for jsonl in slug_dir.glob("*.jsonl"):
                    try:
                        out[str(jsonl)] = jsonl.stat().st_mtime
                    except FileNotFoundError:
                        pass
        return out

    def _prime(self) -> None:
        self._state = self._scan()

    def _loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(self.poll_interval)
            try:
                current = self._scan()
                for path, mtime in current.items():
                    prev = self._state.get(path)
                    if prev is None:
                        self.emit({
                            "type": "jsonl.created",
                            "path": path,
                            "slug": pathlib.Path(path).parent.name,
                        })
                    elif mtime > prev:
                        self.emit({
                            "type": "jsonl.updated",
                            "path": path,
                            "slug": pathlib.Path(path).parent.name,
                        })
                for path in set(self._state) - set(current):
                    self.emit({
                        "type": "jsonl.removed",
                        "path": path,
                        "slug": pathlib.Path(path).parent.name,
                    })
                self._state = current
            except Exception as e:
                self.emit({"type": "watcher.error", "error": str(e)})
