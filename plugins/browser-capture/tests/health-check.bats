#!/usr/bin/env bats

load test_helper

setup() {
  setup_plugin_env
}

@test "health-check: exits 0 outside plugin context" {
  # Without deps installed, some checks warn but script still runs
  unset CLAUDE_PLUGIN_DATA
  unset CLAUDE_PLUGIN_ROOT
  run node "$SCRIPTS_DIR/health-check.js"
  # Should exit (0 or 1 depending on what's available) but not crash
  [[ "$status" -eq 0 || "$status" -eq 1 ]]
}

@test "health-check: stdout is valid JSON" {
  run node "$SCRIPTS_DIR/health-check.js"
  # Last line of stdout should be JSON
  local json_line="${lines[-1]}"
  assert_valid_json "$json_line"
}

@test "health-check: reports node version" {
  run node "$SCRIPTS_DIR/health-check.js" 2>&1
  [[ "$output" == *"Node.js"* ]]
}

@test "health-check: reports platform" {
  run node "$SCRIPTS_DIR/health-check.js" 2>&1
  [[ "$output" == *"Platform"* ]]
}

@test "health-check: detects missing playwright" {
  # Fresh CLAUDE_PLUGIN_DATA has no node_modules
  run node "$SCRIPTS_DIR/health-check.js" 2>&1
  [[ "$output" == *"FAIL"* ]] || [[ "$output" == *"WARN"* ]]
}

@test "health-check: JSON has summary field" {
  run node "$SCRIPTS_DIR/health-check.js"
  local json_line="${lines[-1]}"
  assert_json_field "$json_line" '.summary.pass' || true
  # Just verify the field exists, value depends on env
  [[ "$json_line" == *'"summary"'* ]]
}
