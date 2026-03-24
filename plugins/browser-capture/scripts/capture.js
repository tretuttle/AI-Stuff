// Self-resolve dependencies -- must be FIRST thing in the file (D-07)
const path = require('path');
const fs = require('fs');
const Module = require('module');

function resolveModules() {
  const candidates = [];
  // Check CLAUDE_PLUGIN_DATA first (D-06)
  if (process.env.CLAUDE_PLUGIN_DATA) {
    candidates.push(path.join(process.env.CLAUDE_PLUGIN_DATA, 'node_modules'));
  }
  // Check NODE_PATH if set (command/skill files may pass this)
  if (process.env.NODE_PATH) {
    for (const p of process.env.NODE_PATH.split(path.delimiter)) {
      if (p && !candidates.includes(p)) {
        candidates.push(p);
      }
    }
  }
  // Sibling node_modules (for local dev)
  candidates.push(path.join(__dirname, '..', 'node_modules'));
  // Local node_modules
  candidates.push(path.join(__dirname, 'node_modules'));

  for (const dir of candidates) {
    if (fs.existsSync(path.join(dir, 'playwright'))) {
      process.env.NODE_PATH = dir;
      Module._initPaths();
      return true;
    }
  }
  return false;
}

if (!resolveModules()) {
  process.stderr.write(JSON.stringify({
    success: false,
    error: 'Dependencies not found. Run the plugin SessionStart hook or manually: npm install playwright js-beautify'
  }) + '\n');
  process.exit(1);
}

// NOW safe to require external deps
const crypto = require('crypto');
const { chromium } = require('playwright');
const { js: beautifyJs, css: beautifyCss, html: beautifyHtml } = require('js-beautify');

function parseArgs(argv) {
  const args = {
    urls: [],
    output: './browser-capture-output',  // D-04
    beautify: true,      // D-05: beautify ON by default
    allDomains: true,    // D-05: all-domains ON
    noContent: true,     // D-05: no-content markers ON
    dataUris: true,      // D-05: data-uri extraction ON
    followLinks: false,
    followDepth: 1,
    cookiesFrom: null,       // browser name (e.g. 'chrome', 'brave')
    cookieDomains: null,     // specific domains to import, or null for all
    cookieProfile: 'Default', // browser profile name
  };

  let i = 2; // skip 'node' and script path
  while (i < argv.length) {
    switch (argv[i]) {
      case '--urls':  // D-03: variadic, consumes until next --flag
        i++;
        while (i < argv.length && !argv[i].startsWith('--')) {
          args.urls.push(argv[i++]);
        }
        break;
      case '--output':
        args.output = argv[++i];
        i++;
        break;
      case '--no-beautify':
        args.beautify = false;
        i++;
        break;
      case '--single-domain':
        args.allDomains = false;
        i++;
        break;
      case '--skip-no-content':
        args.noContent = false;
        i++;
        break;
      case '--skip-data-uris':
        args.dataUris = false;
        i++;
        break;
      case '--follow-links':
        args.followLinks = true;
        i++;
        break;
      case '--follow-depth':
        args.followDepth = parseInt(argv[++i], 10) || 1;
        i++;
        break;
      case '--cookies-from':
        args.cookiesFrom = argv[++i];
        i++;
        break;
      case '--cookie-domains':
        args.cookieDomains = argv[++i].split(',').map(d => d.trim()).filter(Boolean);
        i++;
        break;
      case '--cookie-profile':
        args.cookieProfile = argv[++i];
        i++;
        break;
      default:
        i++;
    }
  }
  return args;
}

let OUTPUT_DIR;

// Track all captured resources globally
const allResources = new Map(); // requestId -> resource info
const responseBodyMap = new Map(); // requestId -> body buffer
const pendingRequests = new Map(); // requestId -> resolve function

function urlToFilePath(urlStr) {
  try {
    // Handle data: URIs — hash the content to produce a short, safe filename
    if (urlStr.startsWith('data:')) {
      const hash = crypto.createHash('sha1').update(urlStr).digest('hex').substring(0, 12);
      // Extract MIME type: data:image/svg+xml;... or data:image/png;base64,...
      const mimeMatch = urlStr.match(/^data:([^;,]+)/);
      const mime = mimeMatch ? mimeMatch[1] : 'application/octet-stream';
      const ext = mime.split('/')[1]?.split('+')[0] || 'bin';
      return path.join('_data-uris', hash + '.' + ext);
    }

    const u = new URL(urlStr);
    let pathname = u.pathname;
    // Remove trailing slash
    pathname = pathname.replace(/\/$/, '');
    // Default empty pathname to /index (root page)
    if (!pathname) {
      pathname = '/index';
    }
    // Check extension on PATHNAME only (not hostname) to avoid
    // TLDs like .tech/.app/.design being mistaken for file extensions
    const ext = path.extname(pathname);
    if (!ext || ext === '.') {
      pathname += '.html';
    }
    let filePath = u.hostname + pathname;
    // Remove query string from path but keep it identifiable
    if (u.search) {
      const safeQuery = u.search.replace(/[?&=]/g, '_').substring(0, 80);
      const parsed = path.parse(filePath);
      filePath = path.join(parsed.dir, parsed.name + safeQuery + parsed.ext);
    }
    return filePath;
  } catch {
    return 'unknown/' + Date.now();
  }
}

function beautify(content, mimeType, filePath) {
  try {
    if (!content || typeof content !== 'string') return content;
    if (mimeType?.includes('javascript') || filePath?.endsWith('.js')) {
      return beautifyJs(content, { indent_size: 2 });
    }
    if (mimeType?.includes('css') || filePath?.endsWith('.css')) {
      return beautifyCss(content, { indent_size: 2 });
    }
    if (mimeType?.includes('html') || filePath?.endsWith('.html')) {
      return beautifyHtml(content, { indent_size: 2 });
    }
  } catch {
    // If beautification fails, return original
  }
  return content;
}

function extractDataUris(content, pageUrl) {
  const dataUriRegex = /data:([^;]+);base64,([A-Za-z0-9+/=]+)/g;
  const extracted = [];
  let match;
  let index = 0;
  while ((match = dataUriRegex.exec(content)) !== null) {
    const mimeType = match[1];
    const base64Data = match[2];
    const ext = mimeType.split('/')[1]?.split('+')[0] || 'bin';
    const fileName = `datauri_${index++}.${ext}`;
    extracted.push({ fileName, mimeType, base64Data });
  }
  return extracted;
}

function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
}

function writeResource(relPath, content, isBase64 = false) {
  const fullPath = path.join(OUTPUT_DIR, relPath);
  ensureDir(fullPath);
  if (isBase64) {
    fs.writeFileSync(fullPath, Buffer.from(content, 'base64'));
  } else {
    fs.writeFileSync(fullPath, content, 'utf-8');
  }
  process.stderr.write('  Wrote: ' + relPath + '\n');
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function waitForNetworkIdle(page, timeout = 15000) {
  try {
    await page.waitForLoadState('networkidle', { timeout });
  } catch {
    process.stderr.write('  Network idle timeout, continuing...\n');
  }
  await sleep(2000); // Extra settle time
}

async function capturePage(cdpSession, page, url, pageMetadata, args) {
  process.stderr.write('\nNavigating to: ' + url + '\n');

  const pageResources = new Map();
  const networkResponses = new Map();

  // Track responses from CDP
  const onResponse = (params) => {
    const { requestId, response } = params;
    networkResponses.set(requestId, {
      url: response.url,
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
      mimeType: response.mimeType,
      fromCache: response.fromDiskCache || response.fromServiceWorker || false,
      timing: response.timing,
      protocol: response.protocol,
      resourceType: null, // filled by requestWillBeSent
    });
  };

  const requestTypes = new Map();
  const onRequest = (params) => {
    requestTypes.set(params.requestId, params.type);
  };

  const onLoadingFinished = (params) => {
    const { requestId, encodedDataLength } = params;
    const resp = networkResponses.get(requestId);
    if (resp) {
      resp.encodedDataLength = encodedDataLength;
      resp.resourceType = requestTypes.get(requestId) || 'Other';
      pageResources.set(requestId, resp);
    }
  };

  cdpSession.on('Network.responseReceived', onResponse);
  cdpSession.on('Network.requestWillBeSent', onRequest);
  cdpSession.on('Network.loadingFinished', onLoadingFinished);

  // Navigate
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await waitForNetworkIdle(page);

  // Now fetch bodies for all captured responses
  process.stderr.write('  Captured ' + pageResources.size + ' network resources\n');

  for (const [requestId, info] of pageResources) {
    try {
      const { body, base64Encoded } = await cdpSession.send('Network.getResponseBody', { requestId });
      info.body = body;
      info.base64Encoded = base64Encoded;
    } catch (e) {
      info.body = null;
      info.bodyError = e.message;
    }
  }

  // Also get resource tree for cached/inline resources
  try {
    const tree = await cdpSession.send('Page.getResourceTree');
    const allFrameResources = [];

    function collectResources(frameTree) {
      if (frameTree.resources) {
        allFrameResources.push(...frameTree.resources);
      }
      if (frameTree.childFrames) {
        for (const child of frameTree.childFrames) {
          collectResources(child);
        }
      }
    }
    collectResources(tree.frameTree);

    process.stderr.write('  Resource tree has ' + allFrameResources.length + ' resources\n');

    for (const res of allFrameResources) {
      // Check if we already have this URL from network capture
      const alreadyCaptured = [...pageResources.values()].some(r => r.url === res.url);
      if (!alreadyCaptured) {
        try {
          const { content, base64Encoded } = await cdpSession.send('Page.getResourceContent', {
            frameId: tree.frameTree.frame.id,
            url: res.url,
          });
          const fakeId = 'tree_' + Math.random().toString(36).substr(2);
          pageResources.set(fakeId, {
            url: res.url,
            status: 200,
            statusText: 'OK (from resource tree)',
            headers: {},
            mimeType: res.mimeType,
            fromCache: true,
            resourceType: res.type,
            body: content,
            base64Encoded: base64Encoded,
            fromResourceTree: true,
          });
        } catch (e) {
          // Still record it as a marker
          const fakeId = 'tree_' + Math.random().toString(36).substr(2);
          pageResources.set(fakeId, {
            url: res.url,
            mimeType: res.mimeType,
            resourceType: res.type,
            body: null,
            bodyError: e.message,
            fromResourceTree: true,
          });
        }
      }
    }
  } catch (e) {
    process.stderr.write('  Resource tree error: ' + e.message + '\n');
  }

  // Remove listeners
  cdpSession.off('Network.responseReceived', onResponse);
  cdpSession.off('Network.requestWillBeSent', onRequest);
  cdpSession.off('Network.loadingFinished', onLoadingFinished);

  // Write resources to disk
  const metadata = [];
  for (const [requestId, info] of pageResources) {
    const relPath = urlToFilePath(info.url);
    const entry = {
      pageUrl: url,
      url: info.url,
      filePath: relPath,
      status: info.status,
      statusText: info.statusText,
      headers: info.headers || {},
      mimeType: info.mimeType,
      resourceType: info.resourceType,
      fromCache: info.fromCache || false,
      fromResourceTree: info.fromResourceTree || false,
      encodedDataLength: info.encodedDataLength,
      timing: info.timing,
      protocol: info.protocol,
      hasContent: info.body !== null && info.body !== undefined,
      bodyError: info.bodyError || null,
    };
    metadata.push(entry);

    try {
      if (info.body != null) {
        let content = info.body;
        let isBase64 = info.base64Encoded;

        // Beautify text content (gated by args.beautify)
        if (!isBase64 && typeof content === 'string') {
          if (args.beautify) {
            content = beautify(content, info.mimeType, relPath);
          }

          // Extract data URIs (gated by args.dataUris)
          if (args.dataUris) {
            const dataUris = extractDataUris(content, info.url);
            if (dataUris.length > 0) {
              const dataUriDir = path.join(path.dirname(relPath), '_DataURI');
              for (const du of dataUris) {
                writeResource(path.join(dataUriDir, du.fileName), du.base64Data, true);
              }
            }
          }
        }

        writeResource(relPath, content, isBase64);
      } else if (args.noContent) {
        // Write marker file (gated by args.noContent)
        writeResource(relPath, `No Content: ${info.url}\nReason: ${info.bodyError || 'unknown'}`);
      }
    } catch (writeErr) {
      process.stderr.write('  Write error for ' + relPath + ': ' + writeErr.message + '\n');
      entry.writeError = writeErr.message;
    }
  }

  return { count: pageResources.size, metadata };
}

async function findAndClickLinks(page, cdpSession, baseUrl, args, depth = 0) {
  if (depth >= args.followDepth) return [];

  // For GitHub pages, find README links and subdirectory links
  const links = await page.evaluate((base) => {
    const anchors = document.querySelectorAll('a[href]');
    const results = [];
    for (const a of anchors) {
      const href = a.href;
      // README files or subdirectories under the current tree
      if (href.startsWith(base) && href !== base) {
        const text = a.textContent.trim();
        // Look for directories (tree/) or files (blob/) under this path
        if (href.includes('/tree/main/') || href.includes('/blob/main/')) {
          results.push({ href, text });
        }
      }
    }
    return results;
  }, baseUrl);

  // Deduplicate
  const seen = new Set();
  const uniqueLinks = links.filter(l => {
    if (seen.has(l.href)) return false;
    seen.add(l.href);
    return true;
  });

  process.stderr.write('  Found ' + uniqueLinks.length + ' sub-links on GitHub page\n');

  // Navigate to each sub-link (limit to reasonable number)
  const subMetadata = [];
  const toVisit = uniqueLinks.slice(0, 30);
  for (const link of toVisit) {
    try {
      const result = await capturePage(cdpSession, page, link.href, null, args);
      subMetadata.push(...result.metadata);
    } catch (e) {
      process.stderr.write('  Error capturing ' + link.href + ': ' + e.message + '\n');
    }
  }
  return subMetadata;
}

function generateSummary(metadata, outputDir) {
  const totalFiles = metadata.filter(m => m.hasContent).length;
  const totalSize = metadata.reduce((sum, m) => sum + (m.encodedDataLength || 0), 0);

  const byDomain = {};
  const byType = {};
  const byStatus = {};

  for (const entry of metadata) {
    try {
      const domain = new URL(entry.url).hostname;
      byDomain[domain] = (byDomain[domain] || 0) + 1;
    } catch {}
    const type = entry.resourceType || 'Unknown';
    byType[type] = (byType[type] || 0) + 1;
    const status = String(entry.status || 'unknown');
    byStatus[status] = (byStatus[status] || 0) + 1;
  }

  let summary = 'Capture Summary\n' + '='.repeat(40) + '\n\n';
  summary += 'Total files: ' + totalFiles + '\n';
  summary += 'Total size: ' + (totalSize / 1024).toFixed(1) + ' KB\n\n';

  summary += 'By Domain:\n';
  for (const [domain, count] of Object.entries(byDomain).sort((a, b) => b[1] - a[1])) {
    summary += '  ' + domain + ': ' + count + '\n';
  }

  summary += '\nBy Resource Type:\n';
  for (const [type, count] of Object.entries(byType).sort((a, b) => b[1] - a[1])) {
    summary += '  ' + type + ': ' + count + '\n';
  }

  summary += '\nBy Status Code:\n';
  for (const [status, count] of Object.entries(byStatus).sort((a, b) => b[1] - a[1])) {
    summary += '  ' + status + ': ' + count + '\n';
  }

  fs.writeFileSync(path.join(outputDir, '_summary.txt'), summary, 'utf-8');
  return { totalFiles, totalSize, domains: Object.keys(byDomain) };
}

async function main() {
  const args = parseArgs(process.argv);

  if (args.urls.length === 0) {
    process.stdout.write(JSON.stringify({ success: false, error: 'No URLs provided. Use --urls <url1> <url2> ...' }) + '\n');
    process.exit(1);
  }

  OUTPUT_DIR = path.resolve(args.output);

  process.stderr.write('Starting capture...\n');
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();
  const cdpSession = await context.newCDPSession(page);

  // Enable CDP domains
  await cdpSession.send('Network.enable');
  await cdpSession.send('Page.enable');

  // Import cookies from a real browser if requested
  if (args.cookiesFrom) {
    try {
      const { importCookies } = require('./cookie-import');
      process.stderr.write('Importing cookies from ' + args.cookiesFrom + '...\n');
      const result = await importCookies(args.cookiesFrom, {
        domains: args.cookieDomains,
        profile: args.cookieProfile,
      });
      if (result.count > 0) {
        await context.addCookies(result.cookies);
        process.stderr.write('  Imported ' + result.count + ' cookies' +
          (result.failed > 0 ? ' (' + result.failed + ' failed to decrypt)' : '') + '\n');
      } else {
        process.stderr.write('  No cookies found' +
          (result.failed > 0 ? ' (' + result.failed + ' failed to decrypt)' : '') + '\n');
      }
    } catch (err) {
      process.stderr.write('  Cookie import failed: ' + err.message + '\n');
      process.stderr.write('  Continuing without cookies.\n');
    }
  }

  const globalMetadata = [];

  // Process each page
  for (const url of args.urls) {
    try {
      const result = await capturePage(cdpSession, page, url, globalMetadata, args);
      globalMetadata.push(...result.metadata);
      process.stderr.write('  Total resources for page: ' + result.count + '\n');

      // For GitHub pages, explore sub-links (gated by args.followLinks)
      if (args.followLinks && url.includes('github.com')) {
        const subMeta = await findAndClickLinks(page, cdpSession, url, args, 0);
        globalMetadata.push(...subMeta);
      }
    } catch (e) {
      process.stderr.write('Error on ' + url + ': ' + e.message + '\n');
    }
  }

  await browser.close();

  // Write consolidated metadata (D-14, CAPT-03)
  const metaPath = path.join(OUTPUT_DIR, '_metadata.json');
  fs.writeFileSync(metaPath, JSON.stringify(globalMetadata, null, 2), 'utf-8');

  // Write summary (D-15, CAPT-04)
  const summaryData = generateSummary(globalMetadata, OUTPUT_DIR);

  process.stderr.write('\nCapture complete!\n');

  // Structured JSON to stdout (D-16, CAPT-05)
  const result = {
    success: true,
    outputDir: path.resolve(OUTPUT_DIR),
    totalFiles: summaryData.totalFiles,
    totalSize: summaryData.totalSize,
    domains: summaryData.domains,
  };
  process.stdout.write(JSON.stringify(result) + '\n');

  // Exit success (D-17, CAPT-06)
  process.exit(0);
}

main().catch(e => {
  process.stderr.write('Fatal error: ' + e.message + '\n');
  process.stdout.write(JSON.stringify({ success: false, error: e.message }) + '\n');
  process.exit(1);
});
