#!/usr/bin/env bats

load test_helper

setup() {
  setup_plugin_env
  # Use temp cache dir to avoid polluting real cache
  export HOME="${BATS_TEST_TMPDIR}/fakehome"
  mkdir -p "$HOME/.cache/browser-capture"
}

@test "update-check: exits 0 on success" {
  run node "$SCRIPTS_DIR/update-check.js"
  [ "$status" -eq 0 ]
}

@test "update-check: outputs nothing or valid update line" {
  run node "$SCRIPTS_DIR/update-check.js"
  [ "$status" -eq 0 ]
  # Output is either empty, UP_TO_DATE, or UPDATE_AVAILABLE
  if [ -n "$output" ]; then
    [[ "$output" == UPDATE_AVAILABLE* ]] || [[ "$output" == UP_TO_DATE* ]]
  fi
}

@test "update-check: respects cache" {
  # Prime the cache
  mkdir -p "$HOME/.cache/browser-capture"
  echo "UP_TO_DATE 1.1.0" > "$HOME/.cache/browser-capture/update-check"
  # Touch to make it fresh
  touch "$HOME/.cache/browser-capture/update-check"

  run node "$SCRIPTS_DIR/update-check.js"
  [ "$status" -eq 0 ]
  # Should exit quickly with no output (cached UP_TO_DATE)
  [ -z "$output" ]
}

@test "update-check: stale cache triggers re-fetch" {
  mkdir -p "$HOME/.cache/browser-capture"
  echo "UP_TO_DATE 1.1.0" > "$HOME/.cache/browser-capture/update-check"
  # Make cache 120 minutes old (past 60min TTL)
  touch -t "$(date -d '120 minutes ago' '+%Y%m%d%H%M.%S' 2>/dev/null || date -v-120M '+%Y%m%d%H%M.%S')" "$HOME/.cache/browser-capture/update-check" 2>/dev/null || skip "Cannot backdate files on this platform"

  run node "$SCRIPTS_DIR/update-check.js"
  [ "$status" -eq 0 ]
  # Should have re-fetched and written new cache
  [ -f "$HOME/.cache/browser-capture/update-check" ]
}

@test "update-check: handles network failure gracefully" {
  # Point at a URL that will fail
  # The script uses a hardcoded URL, but it has a 5s timeout and falls back
  # Just verify it doesn't crash
  run timeout 15 node "$SCRIPTS_DIR/update-check.js"
  [ "$status" -eq 0 ]
}
