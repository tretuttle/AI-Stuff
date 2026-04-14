"""CLI entrypoint: `recon-wrapper serve [--host H] [--port P]`."""
from __future__ import annotations
import argparse
import sys

from .config import Config, ensure_token
from .server import serve


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="recon-wrapper")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("serve", help="Run the HTTP API server")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=7777)

    sub.add_parser("token", help="Print (or generate) the API token")

    args = ap.parse_args(argv)

    if args.cmd == "serve":
        cfg = Config(host=args.host, port=args.port)
        cfg.recon_dir.mkdir(parents=True, exist_ok=True)
        serve(cfg)
        return 0

    if args.cmd == "token":
        cfg = Config()
        cfg.recon_dir.mkdir(parents=True, exist_ok=True)
        print(ensure_token(cfg))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
