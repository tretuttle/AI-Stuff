#!/bin/bash
# PreToolUse hook: Prevent writes to system theme directories
# Themes must be developed in ~/omarchy-theme-workshop/ and installed via GitHub

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [ -z "$file_path" ]; then
  exit 0
fi

# Block writes to omarchy system theme directories
if [[ "$file_path" == *"/.config/omarchy/themes/"* ]] || \
   [[ "$file_path" == *"/.local/share/omarchy/"* ]]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "deny"}, "systemMessage": "Cannot write directly to omarchy system directories. Use ~/omarchy-theme-workshop/ for development, then install via omarchy-theme-install from GitHub."}'
  exit 2
fi

exit 0
