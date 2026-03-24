#!/usr/bin/env node
/**
 * Build browser-capture into a standalone bundle.
 *
 * Uses esbuild to bundle capture.js + all JS dependencies (js-beautify,
 * better-sqlite3, cookie-import) into a single dist/capture.js file.
 *
 * Playwright stays as a runtime dependency since it needs native Chromium,
 * but everything else is inlined — no node_modules resolution at runtime.
 *
 * Also installs Playwright Chromium if not present.
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const PLUGIN_ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.join(__dirname, '..');
const PLUGIN_DATA = process.env.CLAUDE_PLUGIN_DATA || path.join(PLUGIN_ROOT, '.data');
const DIST_DIR = path.join(PLUGIN_DATA, 'dist');
const BUNDLE_PATH = path.join(DIST_DIR, 'capture.js');
const VERSION_FILE = path.join(DIST_DIR, '.build-version');

function getPluginVersion() {
  try {
    return JSON.parse(fs.readFileSync(
      path.join(PLUGIN_ROOT, '.claude-plugin', 'plugin.json'), 'utf-8'
    )).version || 'unknown';
  } catch { return 'unknown'; }
}

function needsBuild() {
  if (!fs.existsSync(BUNDLE_PATH)) return true;
  if (!fs.existsSync(VERSION_FILE)) return true;
  try {
    const built = fs.readFileSync(VERSION_FILE, 'utf-8').trim();
    return built !== getPluginVersion();
  } catch { return true; }
}

function ensureDeps() {
  const nodeModules = path.join(PLUGIN_DATA, 'node_modules');
  const hasPlaywright = fs.existsSync(path.join(nodeModules, 'playwright'));
  const hasBeautify = fs.existsSync(path.join(nodeModules, 'js-beautify'));
  const hasSqlite = fs.existsSync(path.join(nodeModules, 'better-sqlite3'));
  const hasEsbuild = fs.existsSync(path.join(nodeModules, 'esbuild'));

  if (!hasPlaywright || !hasBeautify || !hasSqlite || !hasEsbuild) {
    process.stderr.write('[browser-capture] Installing dependencies...\n');
    fs.mkdirSync(PLUGIN_DATA, { recursive: true });

    // Copy package.json if needed
    const bundledPkg = path.join(PLUGIN_ROOT, 'scripts', 'package.json');
    const dataPkg = path.join(PLUGIN_DATA, 'package.json');
    if (fs.existsSync(bundledPkg)) {
      // Add esbuild as a build dep
      const pkg = JSON.parse(fs.readFileSync(bundledPkg, 'utf-8'));
      pkg.dependencies = pkg.dependencies || {};
      pkg.dependencies.esbuild = '^0.24.0';
      fs.writeFileSync(dataPkg, JSON.stringify(pkg, null, 2));
    }

    execFileSync('npm', ['install', '--production'], {
      cwd: PLUGIN_DATA,
      stdio: 'inherit',
      timeout: 120000,
    });
  }
}

function ensureChromium() {
  // Check if chromium is already installed
  const candidates = [PLUGIN_DATA, path.join(PLUGIN_DATA, 'node_modules', '..')];
  for (const dir of candidates) {
    try {
      const entries = fs.readdirSync(dir);
      if (entries.some(e => e.startsWith('chromium-'))) return;
    } catch {}
  }

  process.stderr.write('[browser-capture] Installing Chromium...\n');
  execFileSync('npx', ['playwright', 'install', 'chromium'], {
    cwd: PLUGIN_DATA,
    stdio: 'inherit',
    timeout: 240000,
    env: {
      ...process.env,
      PLAYWRIGHT_BROWSERS_PATH: PLUGIN_DATA,
    },
  });
}

function bundle() {
  process.stderr.write('[browser-capture] Building capture engine...\n');
  fs.mkdirSync(DIST_DIR, { recursive: true });

  // Use esbuild to bundle. Playwright is external (needs native chromium).
  // better-sqlite3 is external (native C++ addon, can't bundle).
  const esbuild = require(path.join(PLUGIN_DATA, 'node_modules', 'esbuild'));
  esbuild.buildSync({
    entryPoints: [path.join(PLUGIN_ROOT, 'scripts', 'capture.js')],
    bundle: true,
    platform: 'node',
    target: 'node18',
    outfile: BUNDLE_PATH,
    external: ['playwright', 'better-sqlite3'],
    // Inline js-beautify and cookie-import
    format: 'cjs',
    sourcemap: false,
    minify: false, // keep readable for debugging
  });

  // Write version marker
  fs.writeFileSync(VERSION_FILE, getPluginVersion());
  process.stderr.write('[browser-capture] Build complete: ' + BUNDLE_PATH + '\n');
}

function verifyBrowser() {
  try {
    execFileSync('node', [
      '-e',
      'const{chromium}=require("playwright");(async()=>{const b=await chromium.launch();await b.close();process.exit(0)})()'
    ], {
      cwd: PLUGIN_DATA,
      timeout: 15000,
      stdio: 'pipe',
      env: {
        ...process.env,
        NODE_PATH: path.join(PLUGIN_DATA, 'node_modules'),
        PLAYWRIGHT_BROWSERS_PATH: PLUGIN_DATA,
      },
    });
    return true;
  } catch { return false; }
}

try {
  if (!needsBuild()) {
    process.stderr.write('[browser-capture] Engine up to date.\n');
    process.exit(0);
  }

  ensureDeps();
  ensureChromium();
  bundle();

  if (verifyBrowser()) {
    process.stderr.write('[browser-capture] Ready to capture.\n');
  } else {
    process.stderr.write('[browser-capture] Warning: Chromium verification failed. Capture may still work.\n');
  }
} catch (err) {
  process.stderr.write('[browser-capture] Build failed: ' + err.message + '\n');
  process.exit(1);
}
