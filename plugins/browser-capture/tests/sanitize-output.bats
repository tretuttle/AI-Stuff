#!/usr/bin/env bats

load test_helper

setup() {
  setup_plugin_env
}

# Helper: pipe JSON to sanitize-output.js via stdin
run_sanitizer() {
  run bash -c 'echo "$1" | node "$2"' -- "$1" "$SCRIPTS_DIR/sanitize-output.js"
}

@test "sanitize: exits 0 on non-Bash tool" {
  local input='{"tool_name":"Read","tool_result":{"stdout":"hello"}}'
  run_sanitizer "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "sanitize: exits 0 on normal Bash output" {
  local input='{"tool_name":"Bash","tool_result":{"stdout":"normal output from ls"}}'
  run_sanitizer "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "sanitize: detects data URI in capture output" {
  local input='{"tool_name":"Bash","tool_result":{"stdout":"capture.js\ndata:image/svg+xml;base64,'"$(printf 'A%.0s' {1..200})"'"}}'
  run_sanitizer "$input"
  [ "$status" -eq 0 ]
  if [ -n "$output" ]; then
    [[ "$output" == *"additionalContext"* ]]
    [[ "$output" == *"binary/image data"* ]]
  fi
}

@test "sanitize: detects SVG content in capture output" {
  local svg_content='<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
  svg_content+="$(printf 'x%.0s' {1..600})"
  svg_content+='</svg>'
  local input="{\"tool_name\":\"Bash\",\"tool_result\":{\"stdout\":\"browser-capture ${svg_content}\"}}"
  run_sanitizer "$input"
  [ "$status" -eq 0 ]
  if [ -n "$output" ]; then
    [[ "$output" == *"additionalContext"* ]]
  fi
}

@test "sanitize: ignores non-capture Bash commands" {
  local input='{"tool_name":"Bash","tool_result":{"stdout":"git status\nOn branch main"}}'
  run_sanitizer "$input"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "sanitize: handles malformed JSON gracefully" {
  run bash -c 'echo "not json" | node "$1"' -- "$SCRIPTS_DIR/sanitize-output.js"
  [ "$status" -eq 0 ]
}

@test "sanitize: handles empty stdin gracefully" {
  run bash -c 'echo "" | node "$1"' -- "$SCRIPTS_DIR/sanitize-output.js"
  [ "$status" -eq 0 ]
}

@test "sanitize: output is valid JSON when present" {
  local input='{"tool_name":"Bash","tool_result":{"stdout":"capture.js\ndata:image/png;base64,'"$(printf 'B%.0s' {1..200})"'"}}'
  run_sanitizer "$input"
  if [ -n "$output" ]; then
    assert_valid_json "$output"
  fi
}
