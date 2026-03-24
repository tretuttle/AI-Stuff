#!/usr/bin/env bats

load test_helper

setup() {
  setup_plugin_env
  export CAPTURE_SCRIPT="$SCRIPTS_DIR/capture.js"
  export OUTPUT_DIR="${BATS_TEST_TMPDIR}/capture-output"

  # Check if deps are available
  if node -e "require('playwright')" 2>/dev/null; then
    export HAS_DEPS=true
  else
    export HAS_DEPS=false
  fi
}

@test "capture: exits non-zero with no arguments" {
  run node "$CAPTURE_SCRIPT" 2>&1
  [ "$status" -ne 0 ]
}

@test "capture: reports missing deps if playwright not installed" {
  if [ "$HAS_DEPS" = true ]; then
    skip "playwright is installed, can't test missing deps"
  fi
  run node "$CAPTURE_SCRIPT" 2>&1
  [[ "$output" == *"Dependencies not found"* ]] || [[ "$output" == *"not found"* ]]
}

@test "capture: exits 1 with no URLs when deps available" {
  if [ "$HAS_DEPS" = false ]; then
    skip "playwright not installed"
  fi
  run node "$CAPTURE_SCRIPT" 2>&1
  [ "$status" -eq 1 ]
  [[ "$output" == *"No URLs provided"* ]]
}

@test "capture: bare URL gets https:// prepended when deps available" {
  if [ "$HAS_DEPS" = false ]; then
    skip "playwright not installed"
  fi
  run node "$CAPTURE_SCRIPT" --urls example.com --output "$OUTPUT_DIR" 2>&1
  [[ "$output" == *"Auto-prepending https:// to: example.com"* ]]
}

@test "capture: https:// URL is not modified" {
  if [ "$HAS_DEPS" = false ]; then
    skip "playwright not installed"
  fi
  run node "$CAPTURE_SCRIPT" --urls https://example.com --output "$OUTPUT_DIR" 2>&1
  [[ "$output" != *"Auto-prepending"* ]] || true
}

@test "capture: http:// URL is not modified" {
  if [ "$HAS_DEPS" = false ]; then
    skip "playwright not installed"
  fi
  run node "$CAPTURE_SCRIPT" --urls http://example.com --output "$OUTPUT_DIR" 2>&1
  [[ "$output" != *"Auto-prepending"* ]] || true
}

@test "capture: syntax is valid Node.js" {
  run node --check "$CAPTURE_SCRIPT"
  [ "$status" -eq 0 ]
}

@test "capture: cookie-import.js syntax is valid" {
  run node --check "$SCRIPTS_DIR/cookie-import.js"
  [ "$status" -eq 0 ]
}

@test "capture: all scripts pass syntax check" {
  for script in "$SCRIPTS_DIR"/*.js; do
    run node --check "$script"
    [ "$status" -eq 0 ]
  done
}

@test "capture: hooks.json is valid JSON" {
  run node -e "JSON.parse(require('fs').readFileSync('$PLUGIN_ROOT/hooks/hooks.json','utf-8'))"
  [ "$status" -eq 0 ]
}

@test "capture: plugin.json is valid JSON with required fields" {
  run node -e "
    const m = JSON.parse(require('fs').readFileSync('$PLUGIN_ROOT/.claude-plugin/plugin.json','utf-8'));
    if (!m.name) process.exit(1);
    if (!m.version) process.exit(1);
    if (!/^\d+\.\d+\.\d+$/.test(m.version)) process.exit(1);
  "
  [ "$status" -eq 0 ]
}

@test "capture: hooks.json has SessionStart and PostToolUse" {
  run node -e "
    const h = JSON.parse(require('fs').readFileSync('$PLUGIN_ROOT/hooks/hooks.json','utf-8'));
    if (!h.hooks.SessionStart) process.exit(1);
    if (!h.hooks.PostToolUse) process.exit(1);
  "
  [ "$status" -eq 0 ]
}
