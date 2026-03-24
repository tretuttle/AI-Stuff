/**
 * Chromium browser cookie import for Node.js
 *
 * Reads and decrypts cookies from real Chromium-based browsers,
 * returning Playwright-compatible cookie objects.
 *
 * Ported from gstack's cookie-import-browser.ts (Bun) to Node.js.
 *
 * Supports macOS and Linux. Decryption pipeline:
 *   1. Find cookie DB from browser profile dir
 *   2. Derive AES key (macOS: Keychain + PBKDF2 iter=1003,
 *      Linux v10: "peanuts" iter=1, Linux v11: secret-tool iter=1)
 *   3. AES-128-CBC decrypt with IV = 16 x 0x20, skip 32-byte prefix
 *   4. Chromium epoch → Unix seconds for expiry
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFile } = require('child_process');

// ─── Browser Registry ───────────────────────────────────────────
// Hardcoded — NEVER interpolate user input into shell commands.

const BROWSER_REGISTRY = [
  { name: 'Chrome',   dataDir: 'Google/Chrome/',              keychainService: 'Chrome Safe Storage',         aliases: ['chrome', 'google-chrome', 'google-chrome-stable'], linuxDataDir: 'google-chrome/',              linuxApplication: 'chrome' },
  { name: 'Chromium', dataDir: 'chromium/',                   keychainService: 'Chromium Safe Storage',       aliases: ['chromium'],                                        linuxDataDir: 'chromium/',                   linuxApplication: 'chromium' },
  { name: 'Arc',      dataDir: 'Arc/User Data/',              keychainService: 'Arc Safe Storage',            aliases: ['arc'] },
  { name: 'Brave',    dataDir: 'BraveSoftware/Brave-Browser/',keychainService: 'Brave Safe Storage',          aliases: ['brave'],                                          linuxDataDir: 'BraveSoftware/Brave-Browser/',linuxApplication: 'brave' },
  { name: 'Edge',     dataDir: 'Microsoft Edge/',             keychainService: 'Microsoft Edge Safe Storage', aliases: ['edge'],                                           linuxDataDir: 'microsoft-edge/',             linuxApplication: 'microsoft-edge' },
  { name: 'Vivaldi',  dataDir: 'Vivaldi/',                    keychainService: 'Vivaldi Safe Storage',        aliases: ['vivaldi'],                                        linuxDataDir: 'vivaldi/',                    linuxApplication: 'vivaldi' },
  { name: 'Opera',    dataDir: 'com.operasoftware.Opera/',    keychainService: 'Opera Safe Storage',          aliases: ['opera'],                                          linuxDataDir: 'opera/',                      linuxApplication: 'opera' },
];

// ─── Key Cache ──────────────────────────────────────────────────
const keyCache = new Map();

// ─── Chromium Epoch ─────────────────────────────────────────────
const CHROMIUM_EPOCH_OFFSET = 11644473600000000n;

function chromiumNow() {
  return BigInt(Date.now()) * 1000n + CHROMIUM_EPOCH_OFFSET;
}

function chromiumEpochToUnix(epoch, hasExpires) {
  if (hasExpires === 0 || epoch === 0 || epoch === 0n) return -1;
  const epochBig = BigInt(epoch);
  const unixMicro = epochBig - CHROMIUM_EPOCH_OFFSET;
  return Number(unixMicro / 1000000n);
}

function mapSameSite(value) {
  switch (value) {
    case 0: return 'None';
    case 1: return 'Lax';
    case 2: return 'Strict';
    default: return 'Lax';
  }
}

// ─── Platform Helpers ───────────────────────────────────────────

function getHostPlatform() {
  if (process.platform === 'darwin' || process.platform === 'linux') return process.platform;
  return null;
}

function getSearchPlatforms() {
  const current = getHostPlatform();
  const order = [];
  if (current) order.push(current);
  for (const p of ['darwin', 'linux']) {
    if (!order.includes(p)) order.push(p);
  }
  return order;
}

function getBaseDir(platform) {
  return platform === 'darwin'
    ? path.join(os.homedir(), 'Library', 'Application Support')
    : path.join(os.homedir(), '.config');
}

function getDataDirForPlatform(browser, platform) {
  return platform === 'darwin' ? browser.dataDir : browser.linuxDataDir || null;
}

// ─── Browser Resolution ─────────────────────────────────────────

function resolveBrowser(nameOrAlias) {
  const needle = nameOrAlias.toLowerCase().trim();
  const found = BROWSER_REGISTRY.find(b =>
    b.aliases.includes(needle) || b.name.toLowerCase() === needle
  );
  if (!found) {
    const supported = BROWSER_REGISTRY.map(b => b.name).join(', ');
    throw new Error(`Unknown browser '${nameOrAlias}'. Supported: ${supported}`);
  }
  return found;
}

function findBrowserMatch(browser, profile) {
  if (/[/\\]|\.\./.test(profile) || /[\x00-\x1f]/.test(profile)) {
    throw new Error(`Invalid profile name: '${profile}'`);
  }
  for (const platform of getSearchPlatforms()) {
    const dataDir = getDataDirForPlatform(browser, platform);
    if (!dataDir) continue;
    const dbPath = path.join(getBaseDir(platform), dataDir, profile, 'Cookies');
    try {
      if (fs.existsSync(dbPath)) {
        return { browser, platform, dbPath };
      }
    } catch {}
  }
  return null;
}

function getBrowserMatch(browser, profile) {
  const match = findBrowserMatch(browser, profile);
  if (match) return match;
  throw new Error(`${browser.name} is not installed or profile '${profile}' not found`);
}

// ─── Installed Browsers ─────────────────────────────────────────

function findInstalledBrowsers() {
  return BROWSER_REGISTRY.filter(browser => {
    if (findBrowserMatch(browser, 'Default') !== null) return true;
    for (const platform of getSearchPlatforms()) {
      const dataDir = getDataDirForPlatform(browser, platform);
      if (!dataDir) continue;
      const browserDir = path.join(getBaseDir(platform), dataDir);
      try {
        const entries = fs.readdirSync(browserDir, { withFileTypes: true });
        if (entries.some(e =>
          e.isDirectory() && e.name.startsWith('Profile ') &&
          fs.existsSync(path.join(browserDir, e.name, 'Cookies'))
        )) return true;
      } catch {}
    }
    return false;
  });
}

// ─── SQLite Access ──────────────────────────────────────────────

function openDb(dbPath, browserName) {
  const Database = require('better-sqlite3');
  try {
    return new Database(dbPath, { readonly: true });
  } catch (err) {
    if (err.message && (err.message.includes('SQLITE_BUSY') || err.message.includes('database is locked'))) {
      return openDbFromCopy(dbPath, browserName);
    }
    throw err;
  }
}

function openDbFromCopy(dbPath, browserName) {
  const Database = require('better-sqlite3');
  const tmpPath = `/tmp/browser-capture-cookies-${browserName.toLowerCase()}-${crypto.randomUUID()}.db`;
  try {
    fs.copyFileSync(dbPath, tmpPath);
    const walPath = dbPath + '-wal';
    const shmPath = dbPath + '-shm';
    if (fs.existsSync(walPath)) fs.copyFileSync(walPath, tmpPath + '-wal');
    if (fs.existsSync(shmPath)) fs.copyFileSync(shmPath, tmpPath + '-shm');

    const db = new Database(tmpPath, { readonly: true });
    const origClose = db.close.bind(db);
    db.close = () => {
      origClose();
      try { fs.unlinkSync(tmpPath); } catch {}
      try { fs.unlinkSync(tmpPath + '-wal'); } catch {}
      try { fs.unlinkSync(tmpPath + '-shm'); } catch {}
    };
    return db;
  } catch {
    try { fs.unlinkSync(tmpPath); } catch {}
    throw new Error(
      `Cookie database is locked (${browserName} may be running). Close ${browserName} and retry.`
    );
  }
}

// ─── Key Derivation ─────────────────────────────────────────────

function deriveKey(password, iterations) {
  return crypto.pbkdf2Sync(password, 'saltysalt', iterations, 16, 'sha1');
}

function getCachedDerivedKey(cacheKey, password, iterations) {
  const cached = keyCache.get(cacheKey);
  if (cached) return cached;
  const derived = deriveKey(password, iterations);
  keyCache.set(cacheKey, derived);
  return derived;
}

function execFileAsync(cmd, args, timeoutMs) {
  return new Promise((resolve, reject) => {
    const proc = execFile(cmd, args, { timeout: timeoutMs, encoding: 'utf-8' }, (err, stdout, stderr) => {
      if (err) {
        err.stderr = stderr;
        reject(err);
      } else {
        resolve({ stdout, stderr });
      }
    });
  });
}

async function getMacKeychainPassword(service) {
  try {
    const { stdout } = await execFileAsync(
      'security', ['find-generic-password', '-s', service, '-w'], 10000
    );
    return stdout.trim();
  } catch (err) {
    const errText = (err.stderr || err.message || '').toLowerCase();
    if (errText.includes('user canceled') || errText.includes('denied') || errText.includes('interaction not allowed')) {
      throw new Error(`Keychain access denied. Click "Allow" in the macOS dialog for "${service}".`);
    }
    if (errText.includes('could not be found') || errText.includes('not found')) {
      throw new Error(`No Keychain entry for "${service}". Is this a Chromium-based browser?`);
    }
    throw new Error(`Could not read Keychain: ${err.message}`);
  }
}

async function getLinuxSecretPassword(browser) {
  const attempts = [
    ['secret-tool', 'lookup', 'Title', browser.keychainService],
  ];
  if (browser.linuxApplication) {
    attempts.push(
      ['secret-tool', 'lookup', 'xdg:schema', 'chrome_libsecret_os_crypt_password_v2', 'application', browser.linuxApplication],
      ['secret-tool', 'lookup', 'xdg:schema', 'chrome_libsecret_os_crypt_password', 'application', browser.linuxApplication],
    );
  }
  for (const [cmd, ...args] of attempts) {
    try {
      const { stdout } = await execFileAsync(cmd, args, 3000);
      const password = stdout.trim();
      if (password.length > 0) return password;
    } catch {}
  }
  return null;
}

async function getDerivedKeys(match) {
  if (match.platform === 'darwin') {
    const password = await getMacKeychainPassword(match.browser.keychainService);
    return new Map([
      ['v10', getCachedDerivedKey(`darwin:${match.browser.keychainService}:v10`, password, 1003)],
    ]);
  }

  const keys = new Map();
  keys.set('v10', getCachedDerivedKey('linux:v10', 'peanuts', 1));

  const linuxPassword = await getLinuxSecretPassword(match.browser);
  if (linuxPassword) {
    keys.set(
      'v11',
      getCachedDerivedKey(`linux:${match.browser.keychainService}:v11`, linuxPassword, 1),
    );
  }
  return keys;
}

// ─── Cookie Decryption ──────────────────────────────────────────

function decryptCookieValue(row, keys) {
  if (row.value && row.value.length > 0) return row.value;

  const ev = Buffer.from(row.encrypted_value);
  if (ev.length === 0) return '';

  const prefix = ev.slice(0, 3).toString('utf-8');
  const key = keys.get(prefix);
  if (!key) throw new Error(`No decryption key for ${prefix} cookies`);

  const ciphertext = ev.slice(3);
  const iv = Buffer.alloc(16, 0x20);
  const decipher = crypto.createDecipheriv('aes-128-cbc', key, iv);
  const plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);

  if (plaintext.length <= 32) return '';
  return plaintext.slice(32).toString('utf-8');
}

function toPlaywrightCookie(row, value) {
  return {
    name: row.name,
    value,
    domain: row.host_key,
    path: row.path || '/',
    expires: chromiumEpochToUnix(row.expires_utc, row.has_expires),
    secure: row.is_secure === 1,
    httpOnly: row.is_httponly === 1,
    sameSite: mapSameSite(row.samesite),
  };
}

// ─── Public API ─────────────────────────────────────────────────

/**
 * Import cookies from a real browser into Playwright-compatible format.
 *
 * @param {string} browserName - Browser name or alias (e.g. 'chrome', 'brave')
 * @param {object} opts
 * @param {string[]} [opts.domains] - Specific domains to import. Empty/null = all.
 * @param {string} [opts.profile='Default'] - Browser profile name
 * @returns {Promise<{cookies: object[], count: number, failed: number}>}
 */
async function importCookies(browserName, opts = {}) {
  const { domains = null, profile = 'Default' } = opts;

  const browser = resolveBrowser(browserName);
  const match = getBrowserMatch(browser, profile);
  const derivedKeys = await getDerivedKeys(match);
  const db = openDb(match.dbPath, browser.name);

  try {
    const now = chromiumNow();

    let rows;
    if (domains && domains.length > 0) {
      const placeholders = domains.map(() => '?').join(',');
      const stmt = db.prepare(
        `SELECT host_key, name, value, encrypted_value, path, expires_utc,
                is_secure, is_httponly, has_expires, samesite
         FROM cookies
         WHERE host_key IN (${placeholders})
           AND (has_expires = 0 OR expires_utc > ?)
         ORDER BY host_key, name`
      );
      rows = stmt.all(...domains, now.toString());
    } else {
      const stmt = db.prepare(
        `SELECT host_key, name, value, encrypted_value, path, expires_utc,
                is_secure, is_httponly, has_expires, samesite
         FROM cookies
         WHERE has_expires = 0 OR expires_utc > ?
         ORDER BY host_key, name`
      );
      rows = stmt.all(now.toString());
    }

    const cookies = [];
    let failed = 0;

    for (const row of rows) {
      try {
        const value = decryptCookieValue(row, derivedKeys);
        cookies.push(toPlaywrightCookie(row, value));
      } catch {
        failed++;
      }
    }

    return { cookies, count: cookies.length, failed };
  } finally {
    db.close();
  }
}

/**
 * List installed browsers that have a cookie database.
 * @returns {{name: string, aliases: string[]}[]}
 */
function listBrowsers() {
  return findInstalledBrowsers().map(b => ({ name: b.name, aliases: b.aliases }));
}

module.exports = { importCookies, listBrowsers, resolveBrowser };
