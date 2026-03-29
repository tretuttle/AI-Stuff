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

Check the existing identity above:
- If it contains `**Schema:** 2` → report its contents and stop. Already current.
- If it exists but has no `**Schema:**` line, or schema is not `2` → outdated. Delete it and proceed with a full scan.
- If no identity file exists → proceed with a full scan.

For a full scan, launch the recon-orchestrator agent with this context.

Launch the recon-orchestrator agent now.
