#!/usr/bin/env node
/**
 * browser-capture health check
 *
 * Verifies that all dependencies, browsers, and paths are correctly
 * configured. Outputs a structured status report.
 *
 * Exit codes:
 *   0 = all checks pass
 *   1 = one or more checks failed
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');

const checks = [];
let hasFailure = false;

function pass(name, detail) {
  checks.push({ status: 'PASS', name, detail });
}

function fail(name, detail, fix) {
  checks.push({ status: 'FAIL', name, detail, fix });
  hasFailure = true;
}

function warn(name, detail) {
  checks.push({ status: 'WARN', name, detail });
}

// Check 1: Node.js version
const nodeVer = process.versions.node;
const [nodeMajor] = nodeVer.split('.').map(Number);
if (nodeMajor >= 18) {
  pass('Node.js', 'v' + nodeVer);
} else {
  fail('Node.js', 'v' + nodeVer + ' (need >= 18)', 'Upgrade Node.js to 18+');
}

// Check 2: Plugin environment variables
const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;
const pluginData = process.env.CLAUDE_PLUGIN_DATA;

if (pluginRoot && fs.existsSync(pluginRoot)) {
  pass('CLAUDE_PLUGIN_ROOT', pluginRoot);
} else if (pluginRoot) {
  fail('CLAUDE_PLUGIN_ROOT', 'Set but path missing: ' + pluginRoot, 'Reinstall plugin');
} else {
  warn('CLAUDE_PLUGIN_ROOT', 'Not set (running outside plugin context)');
}

if (pluginData) {
  pass('CLAUDE_PLUGIN_DATA', pluginData);
} else {
  warn('CLAUDE_PLUGIN_DATA', 'Not set (running outside plugin context)');
}

// Check 3: node_modules / playwright
function findNodeModules() {
  const candidates = [];
  if (pluginData) candidates.push(path.join(pluginData, 'node_modules'));
  if (process.env.NODE_PATH) {
    for (const p of process.env.NODE_PATH.split(path.delimiter)) {
      if (p) candidates.push(p);
    }
  }
  candidates.push(path.join(__dirname, '..', 'node_modules'));
  candidates.push(path.join(__dirname, 'node_modules'));
  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, 'playwright'))) return dir;
  }
  return null;
}

const nodeModulesDir = findNodeModules();
if (nodeModulesDir) {
  pass('playwright', 'Found in ' + nodeModulesDir);
} else {
  fail('playwright', 'Not found in any candidate path', 'Run SessionStart hook or: npm install playwright');
}

// Check 4: js-beautify
if (nodeModulesDir && fs.existsSync(path.join(nodeModulesDir, 'js-beautify'))) {
  pass('js-beautify', 'Found');
} else {
  fail('js-beautify', 'Not found', 'Run: npm install js-beautify');
}

// Check 5: better-sqlite3 (optional, for cookie import)
if (nodeModulesDir && fs.existsSync(path.join(nodeModulesDir, 'better-sqlite3'))) {
  pass('better-sqlite3', 'Found (cookie import available)');
} else {
  warn('better-sqlite3', 'Not found (cookie import with --cookies-from will not work)');
}

// Check 6: Chromium browser
function findChromium() {
  const candidates = [];
  if (process.env.PLAYWRIGHT_BROWSERS_PATH) candidates.push(process.env.PLAYWRIGHT_BROWSERS_PATH);
  if (pluginData) candidates.push(pluginData);
  if (nodeModulesDir) candidates.push(path.dirname(nodeModulesDir));
  candidates.push(path.join(__dirname, '..'));
  for (const dir of candidates) {
    try {
      const entries = fs.readdirSync(dir);
      const chromium = entries.find(e => e.startsWith('chromium-'));
      if (chromium) return path.join(dir, chromium);
    } catch {}
  }
  return null;
}

const chromiumDir = findChromium();
if (chromiumDir) {
  pass('Chromium', chromiumDir);
} else {
  fail('Chromium', 'No chromium-* directory found', 'Run: npx playwright install chromium');
}

// Check 7: Install marker
if (pluginData) {
  const marker = path.join(pluginData, '.install-ok');
  if (fs.existsSync(marker)) {
    try {
      const info = JSON.parse(fs.readFileSync(marker, 'utf-8'));
      pass('Install marker', 'OK (installed ' + info.timestamp + ')');
    } catch {
      pass('Install marker', 'Present but unreadable');
    }
  } else {
    warn('Install marker', 'Missing. Install may be incomplete. Next SessionStart will retry.');
  }
}

// Check 8: capture.js exists
const captureScript = path.join(__dirname, 'capture.js');
if (fs.existsSync(captureScript)) {
  pass('capture.js', captureScript);
} else {
  fail('capture.js', 'Not found at ' + captureScript, 'Plugin installation is corrupt');
}

// Check 9: Disk space
try {
  const df = execFileSync('df', ['-h', pluginData || os.tmpdir()], { encoding: 'utf-8', timeout: 5000 });
  const lines = df.trim().split('\n');
  if (lines.length >= 2) {
    const parts = lines[1].split(/\s+/);
    const avail = parts[3];
    const pct = parts[4];
    pass('Disk space', avail + ' available (' + pct + ' used)');
  }
} catch {
  warn('Disk space', 'Could not check');
}

// Check 10: Platform
pass('Platform', process.platform + ' ' + process.arch);

// Output
const output = [];
output.push('browser-capture health check');
output.push('='.repeat(40));
output.push('');

for (const c of checks) {
  const icon = c.status === 'PASS' ? 'OK' : c.status === 'FAIL' ? 'FAIL' : 'WARN';
  const line = '  [' + icon + '] ' + c.name + ': ' + c.detail;
  output.push(line);
  if (c.fix) {
    output.push('        Fix: ' + c.fix);
  }
}

output.push('');
const passCount = checks.filter(c => c.status === 'PASS').length;
const failCount = checks.filter(c => c.status === 'FAIL').length;
const warnCount = checks.filter(c => c.status === 'WARN').length;
output.push(passCount + ' passed, ' + failCount + ' failed, ' + warnCount + ' warnings');

if (hasFailure) {
  output.push('');
  output.push('Some checks failed. Capture may not work correctly.');
}

process.stderr.write(output.join('\n') + '\n');
process.stdout.write(JSON.stringify({
  success: !hasFailure,
  checks: checks,
  summary: { pass: passCount, fail: failCount, warn: warnCount },
}) + '\n');

process.exit(hasFailure ? 1 : 0);
