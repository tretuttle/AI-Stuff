#!/usr/bin/env bash
# Shared test helpers for browser-capture plugin tests

export PLUGIN_ROOT="${BATS_TEST_DIRNAME}/.."
export SCRIPTS_DIR="${PLUGIN_ROOT}/scripts"

# Simulated plugin data directory (per-test isolation)
setup_plugin_env() {
  export CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT"
  export CLAUDE_PLUGIN_DATA="${BATS_TEST_TMPDIR}/plugin-data"
  mkdir -p "$CLAUDE_PLUGIN_DATA"
}

# Assert JSON field value: assert_json_field '{"a":1}' '.a' '1'
assert_json_field() {
  local json="$1" field="$2" expected="$3"
  local actual
  actual=$(echo "$json" | node -e "
    let d='';
    process.stdin.on('data',c=>d+=c);
    process.stdin.on('end',()=>{
      try{console.log(JSON.parse(d)${field})}
      catch{console.log('PARSE_ERROR')}
    })
  ")
  if [ "$actual" != "$expected" ]; then
    echo "JSON field ${field}: expected '${expected}', got '${actual}'"
    echo "Full JSON: $json"
    return 1
  fi
}

# Assert stdout is valid JSON
assert_valid_json() {
  local json="$1"
  node -e "try{JSON.parse(process.argv[1]);process.exit(0)}catch{process.exit(1)}" "$json"
}

# Wait for a condition with timeout
wait_for() {
  local cmd="$1" timeout="${2:-10}" interval="${3:-1}"
  local elapsed=0
  while [ $elapsed -lt $timeout ]; do
    if eval "$cmd" 2>/dev/null; then return 0; fi
    sleep "$interval"
    elapsed=$((elapsed + interval))
  done
  return 1
}
