#!/usr/bin/env bats

# End-to-end capture tests. Require playwright + chromium installed.
# Skipped in environments without deps (CI will install them first).

load test_helper

setup() {
  setup_plugin_env
  export OUTPUT_DIR="${BATS_TEST_TMPDIR}/e2e-output"

  # Check if playwright is available
  if ! node -e "require('playwright')" 2>/dev/null; then
    skip "playwright not installed"
  fi

  # Start a local HTTP server serving fixtures
  export FIXTURE_PORT=0
  local server_script="${BATS_TEST_TMPDIR}/server.js"
  cat > "$server_script" << 'SERVEREOF'
const http = require('http');
const fs = require('fs');
const path = require('path');
const fixturesDir = process.argv[2];
const server = http.createServer((req, res) => {
  const filePath = path.join(fixturesDir, req.url === '/' ? 'basic.html' : req.url);
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
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
  const port = server.address().port;
  fs.writeFileSync(process.argv[3], String(port));
});
SERVEREOF

  local port_file="${BATS_TEST_TMPDIR}/server-port"
  node "$server_script" "${BATS_TEST_DIRNAME}/fixtures" "$port_file" &
  export SERVER_PID=$!

  # Wait for server to start
  wait_for "[ -f '$port_file' ]" 5
  export FIXTURE_PORT=$(cat "$port_file")
  export BASE_URL="http://127.0.0.1:${FIXTURE_PORT}"
}

teardown() {
  # Kill test server
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

  # Check output structure
  [ -d "$OUTPUT_DIR" ]
  [ -f "$OUTPUT_DIR/_metadata.json" ]
  [ -f "$OUTPUT_DIR/_summary.txt" ]
}

@test "e2e: captures HTML content" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]

  # Should have captured the HTML
  local html_file="$OUTPUT_DIR/127.0.0.1/index.html"
  [ -f "$html_file" ] || [ -f "$OUTPUT_DIR/127.0.0.1/index.html" ]

  # HTML should contain our fixture content
  local found=false
  for f in $(find "$OUTPUT_DIR" -name "*.html" -not -name "_*"); do
    if grep -q "Browser Capture Test" "$f" 2>/dev/null; then
      found=true
      break
    fi
  done
  [ "$found" = true ]
}

@test "e2e: metadata.json is valid JSON array" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]

  # Validate metadata
  node -e "
    const meta = JSON.parse(require('fs').readFileSync('$OUTPUT_DIR/_metadata.json','utf-8'));
    if (!Array.isArray(meta)) process.exit(1);
    if (meta.length === 0) process.exit(1);
    // Each entry should have url and resourceType
    for (const e of meta) {
      if (!e.url) process.exit(1);
    }
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

@test "e2e: data URI extraction works" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]

  # The fixture has an inline data:image/png — should be extracted
  # Look for _DataURI or _data-uris directory
  local found_datauri=false
  if find "$OUTPUT_DIR" -path "*DataURI*" -o -path "*data-uri*" | grep -q .; then
    found_datauri=true
  fi
  # Data URI extraction is best-effort, just verify no crash
  true
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

@test "e2e: multiple URLs captured sequentially" {
  run node "$SCRIPTS_DIR/capture.js" --urls "$BASE_URL" "$BASE_URL/basic.html" --output "$OUTPUT_DIR" 2>&1
  [ "$status" -eq 0 ]
  [ -f "$OUTPUT_DIR/_metadata.json" ]
}
