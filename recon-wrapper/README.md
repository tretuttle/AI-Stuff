# recon-wrapper

Frontend-agnostic HTTP + SSE API over the project-recon metadata store and headless Claude Code.

Use it from: Electron, Tauri, MAUI, Vite, OpenTUI, curl, anything that speaks HTTP.

## What it is

- **A read layer** over the metadata the `project-recon` skill already writes (`~/.claude/conversations/*.md`, per-project `.project-identity.md` / `.conversation-identity.md`).
- **A write layer** that triggers recon actions by spawning `claude -p "/project-recon:recon"` (or other prompts) headlessly in a target cwd.
- **An event bus** that emits filesystem notifications when new sessions land.

It does **not** parse jsonl itself. It does **not** reimplement discovery. It wraps the skills.

## Install

```bash
pipx install ./recon-wrapper
# or for dev
cd recon-wrapper && pip install -e .
```

Requires Python 3.11+. Zero hard deps.

## Run

```bash
recon-wrapper serve
# recon-wrapper v0.1.0 on http://127.0.0.1:7777
# token: <random>
# token file: ~/.claude/recon/token
```

Override via env: `RECON_PORT=9000 RECON_HOST=0.0.0.0 recon-wrapper serve` (note: only bind to 0.0.0.0 if you trust your LAN — the bearer token is the only auth).

## Auth

Every request needs `Authorization: Bearer $(cat ~/.claude/recon/token)`.
`/health` and `/schema` are unauthenticated.

## API surface

See `openapi.yaml` for the full contract. Quick tour:

```bash
TOKEN=$(cat ~/.claude/recon/token)
H="Authorization: Bearer $TOKEN"

curl -s http://127.0.0.1:7777/health
curl -s -H "$H" http://127.0.0.1:7777/projects | jq
curl -s -H "$H" http://127.0.0.1:7777/projects/-home-tt-bleakBench | jq
curl -s -H "$H" http://127.0.0.1:7777/projects/-home-tt-bleakBench/context | jq
curl -s -H "$H" http://127.0.0.1:7777/graph | jq

# Trigger a recon run (returns 202 + action id)
curl -s -H "$H" -X POST http://127.0.0.1:7777/actions \
  -d '{"kind":"recon","cwd":"/home/tt/ParkPal3"}' | jq

# Stream its output
curl -N -H "$H" http://127.0.0.1:7777/actions/<id>/stream

# Global event stream (jsonl file events)
curl -N -H "$H" http://127.0.0.1:7777/events
```

## Data shape

Two key schemas live in `src/recon_wrapper/models.py` and are mirrored in `openapi.yaml`:

- `ProjectSummary` / `ProjectDetail` — per-project aggregated view
- `Graph` — cross-project nodes + edges (for viz)

Schema versions are in `recon_wrapper.API_VERSION` and `DATA_VERSION`. Also served at `GET /schema`.

## Architecture

```
                   ┌──────────────────────────────────────────┐
 frontend (any) ─▶ │  HTTP + SSE (stdlib)                     │
                   │   ├─ aggregator  → reads identity .md    │
                   │   ├─ actions     → spawns claude -p      │
                   │   └─ watcher     → polls ~/.claude/projects
                   └──────────────────────────────────────────┘
                                   ▲
                                   │ read-only aggregation
                                   ▼
           ~/.claude/conversations/*.md   ← written by project-recon skills
           ~/.claude/conversation-index.md
           <cwd>/.conversation-identity.md
           <cwd>/.project-identity.md
```

The wrapper owns transport + orchestration only. Data ownership stays with the skills.

## Status

v0.1.0 — initial cut. API and data shapes pinned at 1.0.0. Additive changes are backward compatible; breaking changes bump the schema version.
