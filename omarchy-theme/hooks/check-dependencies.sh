#!/bin/bash
# SessionStart hook: Check theme creation dependencies

set -euo pipefail

missing=()

if ! command -v hellwal &>/dev/null; then
  missing+=("hellwal (run: scripts/setup.sh)")
fi

# Check for tint binary in plugin's bin directory
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$PLUGIN_ROOT" ] && [ ! -x "${PLUGIN_ROOT}/bin/tint" ]; then
  missing+=("tint (run: scripts/setup.sh)")
fi

if ! command -v grim &>/dev/null; then
  missing+=("grim (screenshot tool)")
fi

if ! command -v gh &>/dev/null; then
  missing+=("gh (GitHub CLI)")
fi

if [ ${#missing[@]} -gt 0 ]; then
  msg="omarchy-theme plugin: Missing dependencies - ${missing[*]}"
  echo "{\"systemMessage\": \"$msg\"}"
fi

exit 0
