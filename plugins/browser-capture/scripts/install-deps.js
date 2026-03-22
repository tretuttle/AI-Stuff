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

function fileHash(filePath) {
  const content = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

try {
  // Compare hashes -- skip install if deps are up to date
  if (fs.existsSync(cachedPkg) && fileHash(bundledPkg) === fileHash(cachedPkg)) {
    process.exit(0);
  }

  process.stderr.write('[browser-capture] Installing dependencies...\n');
  fs.mkdirSync(pluginData, { recursive: true });
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

  process.stderr.write('[browser-capture] Dependencies installed successfully.\n');
} catch (err) {
  process.stderr.write('[browser-capture] Install failed: ' + err.message + '\n');
  // Remove cached package.json so next session retries
  try { fs.unlinkSync(cachedPkg); } catch (e) { /* ignore */ }
  process.exit(1);
}
