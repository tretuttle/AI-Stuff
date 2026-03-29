#!/bin/bash
# SessionStart hook: Check theme creation dependencies

set -euo pipefail

missing=()

# Check for binaries in plugin's bin directory
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$PLUGIN_ROOT" ]; then
  if [ ! -x "${PLUGIN_ROOT}/bin/hellwal" ]; then
    missing+=("hellwal (run: ${PLUGIN_ROOT}/scripts/setup.sh)")
  fi
  if [ ! -x "${PLUGIN_ROOT}/bin/tint" ]; then
    missing+=("tint (run: ${PLUGIN_ROOT}/scripts/setup.sh)")
  fi
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
