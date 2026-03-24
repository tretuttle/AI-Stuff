#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');

const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT;
const pluginData = process.env.CLAUDE_PLUGIN_DATA;

if (!pluginRoot || !pluginData) {
  process.stderr.write('[browser-capture] Error: CLAUDE_PLUGIN_ROOT or CLAUDE_PLUGIN_DATA not set. Cannot install dependencies.\n');
  process.exit(1);
}

const bundledPkg = path.join(pluginRoot, 'scripts', 'package.json');
const cachedPkg = path.join(pluginData, 'package.json');
const installMarker = path.join(pluginData, '.install-ok');

function fileHash(filePath) {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

// Check if deps are up to date: hash matches AND install completed successfully last time
function depsUpToDate() {
  if (!fs.existsSync(cachedPkg)) return false;
  if (!fs.existsSync(installMarker)) return false;
  return fileHash(bundledPkg) === fileHash(cachedPkg);
}

// Verify Chromium is actually launchable (like gstack's ensure_playwright_browser)
function verifyBrowser() {
  try {
    execSync(
      'node -e "const{chromium}=require(\'playwright\');(async()=>{const b=await chromium.launch();await b.close();process.exit(0)})()"',
      {
        cwd: pluginData,
        timeout: 15000,
        stdio: 'pipe',
        env: {
          ...process.env,
          NODE_PATH: path.join(pluginData, 'node_modules'),
          PLAYWRIGHT_BROWSERS_PATH: path.resolve(pluginData),
        },
      }
    );
    return true;
  } catch {
    return false;
  }
}

try {
  if (depsUpToDate()) {
    process.exit(0);
  }

  process.stderr.write('[browser-capture] Installing dependencies...\n');
  fs.mkdirSync(pluginData, { recursive: true });

  // Remove install marker BEFORE starting — only re-create it after full success.
  // This prevents the hash check from passing if a previous install was partial.
  try { fs.unlinkSync(installMarker); } catch {}

  // Copy package.json to data dir for npm install
  fs.copyFileSync(bundledPkg, cachedPkg);

  execSync('npm install --production', {
    cwd: pluginData,
    stdio: 'inherit',
    timeout: 120000,
  });

  process.stderr.write('[browser-capture] Installing Chromium browser...\n');
  execSync('npx playwright install chromium', {
    cwd: pluginData,
    stdio: 'inherit',
    timeout: 240000,
    env: {
      ...process.env,
      PLAYWRIGHT_BROWSERS_PATH: path.resolve(pluginData),
    },
  });

  // Verify Chromium actually launches (catches broken installs early)
  process.stderr.write('[browser-capture] Verifying browser launch...\n');
  if (verifyBrowser()) {
    // Mark install as complete — only written after everything succeeds
    fs.writeFileSync(installMarker, JSON.stringify({
      version: require(bundledPkg).version || 'unknown',
      hash: fileHash(bundledPkg),
      timestamp: new Date().toISOString(),
      node: process.version,
      platform: process.platform,
    }, null, 2));
    process.stderr.write('[browser-capture] Setup complete. Ready to capture.\n');
  } else {
    process.stderr.write('[browser-capture] Warning: Chromium installed but failed launch verification.\n');
    process.stderr.write('[browser-capture] Capture may still work — continuing.\n');
    // Don't write marker so next session retries
  }
} catch (err) {
  process.stderr.write('[browser-capture] Install failed: ' + err.message + '\n');
  // Remove both markers so next session retries from scratch
  try { fs.unlinkSync(cachedPkg); } catch {}
  try { fs.unlinkSync(installMarker); } catch {}
  process.exit(1);
}
