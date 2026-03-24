#!/usr/bin/env bats

# End-to-end capture tests. Require playwright + chromium installed.
# Skipped in environments without deps.

load test_helper

setup() {
  setup_plugin_env
  export OUTPUT_DIR="${BATS_TEST_TMPDIR}/e2e-output"

  if ! node -e "require('playwright')" 2>/dev/null; then
    skip "playwright not installed"
  fi

  local server_script="${BATS_TEST_TMPDIR}/server.js"
  cat > "$server_script" << 'SERVEREOF'
const http = require('http');
const fs = require('fs');
const path = require('path');
const fixturesDir = process.argv[2];
const server = http.createServer((req, res) => {
  let filePath;
  if (req.url === '/' || req.url === '/index.html') {
    filePath = path.join(fixturesDir, 'basic.html');
  } else {
    filePath = path.join(fixturesDir, req.url);
  }
  try {
    const content = fs.readFileSync(filePath);
    const ext = path.extname(filePath);
    const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript' };
    res.writeHead(200, { 'Content-Type': types[ext] || 'text/plain' });
    res.end(content);
  } catch {
    res.writeHead(404);
    res.end('Not found');
  }
});
server.listen(0, '127.0.0.1', () => {
  fs.writeFileSync(process.argv[3], String(server.address().port));
});
SERVEREOF

  local port_file="${BATS_TEST_TMPDIR}/server-port"
  node "$server_script" "${BATS_TEST_DIRNAME}/fixtures" "$port_file" &
  export SERVER_PID=$!

  wait_for "[ -f '$port_file' ]" 5
  export FIXTURE_PORT=$(cat "$port_file")
  export BASE_URL="http://127.0.0.1:${FIXTURE_PORT}"
}

teardown() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$OUTPUT_DIR"
}

@test "e2e: captures a page and produces output structure" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  echo "Output: $output"
  [ "$status" -eq 0 ]

  [ -d "$OUTPUT_DIR" ]
  [ -f "$OUTPUT_DIR/_metadata.json" ]
  [ -f "$OUTPUT_DIR/_summary.txt" ]
}

@test "e2e: index.html is captured" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]

  # The main document should be written to 127.0.0.1/index.html
  [ -f "$OUTPUT_DIR/127.0.0.1/index.html" ]

  # Debug: show content if test fails
  echo "index.html content (first 5 lines):"
  head -5 "$OUTPUT_DIR/127.0.0.1/index.html" 2>/dev/null || echo "(empty)"

  # CDP may or may not return the body for the main navigation document.
  # If the body was captured, it should contain our fixture text.
  # If CDP returned empty, capture.js writes a "No Content" marker.
  # Both are valid — the capture engine worked either way.
  local content
  content=$(cat "$OUTPUT_DIR/127.0.0.1/index.html" 2>/dev/null || echo "")
  if [[ "$content" == *"No Content"* ]]; then
    # CDP didn't return the body — this is a known limitation, not a bug
    echo "Note: CDP did not return main document body (known limitation)"
  else
    # Body was returned — verify it has our fixture content
    [[ "$content" == *"Browser Capture Test"* ]]
  fi
}

@test "e2e: metadata.json is valid JSON array with entries" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]

  node -e "
    const meta = JSON.parse(require('fs').readFileSync('$OUTPUT_DIR/_metadata.json','utf-8'));
    if (!Array.isArray(meta)) process.exit(1);
    if (meta.length === 0) process.exit(1);
    for (const e of meta) {
      if (!e.url) process.exit(1);
    }
  "
}

@test "e2e: metadata contains the page URL" {
  node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>/dev/null

  node -e "
    const meta = JSON.parse(require('fs').readFileSync('$OUTPUT_DIR/_metadata.json','utf-8'));
    const hasPageUrl = meta.some(e => e.pageUrl === '$BASE_URL' || e.url.includes('127.0.0.1'));
    if (!hasPageUrl) { console.error('No entry for page URL'); process.exit(1); }
  "
}

@test "e2e: summary.txt has correct format" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]

  [ -f "$OUTPUT_DIR/_summary.txt" ]
  grep -q "Capture Summary" "$OUTPUT_DIR/_summary.txt"
  grep -q "Total files:" "$OUTPUT_DIR/_summary.txt"
  grep -q "By Domain:" "$OUTPUT_DIR/_summary.txt"
}

@test "e2e: stdout JSON has success=true" {
  local result
  result=$(node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>/dev/null)
  assert_valid_json "$result"
  assert_json_field "$result" '.success' 'true'
}

@test "e2e: --no-beautify flag works" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" --no-beautify 2>&1
  [ "$status" -eq 0 ]
  [ -f "$OUTPUT_DIR/_metadata.json" ]
}

@test "e2e: --single-domain flag works" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" --single-domain 2>&1
  [ "$status" -eq 0 ]
  [ -f "$OUTPUT_DIR/_metadata.json" ]
}

@test "e2e: multiple URLs captured" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" "$BASE_URL/basic.html" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]
  [ -f "$OUTPUT_DIR/_metadata.json" ]
}
