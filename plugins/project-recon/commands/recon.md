---
description: Identify this project, find what it belongs to, and write identity files
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent
---

## Context

- Current directory: !`pwd`
- Directory contents: !`ls -la`
- Git info: !`git log --oneline -5 2>/dev/null || echo "Not a git repo"` / !`git remote -v 2>/dev/null || echo "No remotes"`
- Existing identity: !`cat .project-identity.md 2>/dev/null || echo "No identity file yet"`

## Task

If a `.project-identity.md` already exists above, report its contents and stop. Do not re-scan.

Otherwise, launch the recon-orchestrator agent with this context to perform a full scan.

Launch the recon-orchestrator agent now.
