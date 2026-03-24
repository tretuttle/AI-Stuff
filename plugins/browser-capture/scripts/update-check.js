#!/usr/bin/env node
/**
 * browser-capture update checker
 *
 * Compares installed plugin version against the latest on GitHub.
 * Caches results to avoid hitting GitHub on every invocation.
 *
 * Output (one line, or nothing):
 *   UPDATE_AVAILABLE <installed> <remote>
 *   UP_TO_DATE <version>
 *   (nothing on error or if check is cached)
 *
 * Cache: ~/.cache/browser-capture/update-check
 *   UP_TO_DATE: 60 min TTL
 *   UPDATE_AVAILABLE: 720 min TTL (12 hours)
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const os = require('os');

const CACHE_DIR = path.join(os.homedir(), '.cache', 'browser-capture');
const CACHE_FILE = path.join(CACHE_DIR, 'update-check');
const REMOTE_URL = 'https://raw.githubusercontent.com/tretuttle/AI-Stuff/master/plugins/browser-capture/.claude-plugin/plugin.json';

// Read local version
function getLocalVersion() {
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
  const manifestPath = path.join(pluginRoot, '.claude-plugin', 'plugin.json');
  try {
    return JSON.parse(fs.readFileSync(manifestPath, 'utf-8')).version || 'unknown';
  } catch {
    return 'unknown';
  }
}

// Fetch remote version with timeout
function fetchRemoteVersion(timeoutMs) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), timeoutMs);
    const req = https.get(REMOTE_URL, { timeout: timeoutMs }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        clearTimeout(timer);
        try {
          const version = JSON.parse(data).version;
          resolve(version && /^\d+\.\d+/.test(version) ? version : null);
        } catch {
          resolve(null);
        }
      });
    });
    req.on('error', () => { clearTimeout(timer); resolve(null); });
  });
}

// Cache helpers
function readCache() {
  try {
    if (!fs.existsSync(CACHE_FILE)) return null;
    const content = fs.readFileSync(CACHE_FILE, 'utf-8').trim();
    const stat = fs.statSync(CACHE_FILE);
    const ageMinutes = (Date.now() - stat.mtimeMs) / 60000;

    if (content.startsWith('UP_TO_DATE') && ageMinutes < 60) return content;
    if (content.startsWith('UPDATE_AVAILABLE') && ageMinutes < 720) return content;
    return null; // stale
  } catch {
    return null;
  }
}

function writeCache(line) {
  try {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    fs.writeFileSync(CACHE_FILE, line + '\n');
  } catch {}
}

async function main() {
  const localVer = getLocalVersion();
  if (localVer === 'unknown') process.exit(0);

  // Check cache
  const cached = readCache();
  if (cached) {
    // Only output UPDATE_AVAILABLE from cache (not UP_TO_DATE)
    if (cached.startsWith('UPDATE_AVAILABLE')) {
      process.stdout.write(cached + '\n');
    }
    process.exit(0);
  }

  // Fetch remote
  const remoteVer = await fetchRemoteVersion(5000);
  if (!remoteVer) {
    writeCache('UP_TO_DATE ' + localVer); // assume OK on fetch failure
    process.exit(0);
  }

  if (localVer === remoteVer) {
    writeCache('UP_TO_DATE ' + localVer);
    process.exit(0);
  }

  const line = 'UPDATE_AVAILABLE ' + localVer + ' ' + remoteVer;
  writeCache(line);
  process.stdout.write(line + '\n');
}

main().catch(() => process.exit(0));
