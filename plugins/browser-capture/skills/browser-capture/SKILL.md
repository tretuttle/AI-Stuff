---
name: browser-capture
description: >
  Use when the user wants to capture, record, or archive what a browser loads from a website.
  Triggers on phrases like: "capture everything from this site", "record what the browser loads",
  "archive the page resources", "save all resources", "grab everything the browser receives",
  "capture the network traffic and resources", "do a browser capture of", "run a capture on",
  "what does this page load", "get me all the JS/CSS/assets from",
  "download all resources", "what network requests does this make", "intercept browser traffic".
  Do NOT use for normal web browsing, page summarization, scraping text content, or completing tasks on a page.
  This skill is for the security/reverse-engineering/endpoint-discovery workflow where the user
  wants a complete offline archive of every resource the browser receives during navigation.
---

# Browser Resource Capture

You have access to a Playwright+CDP browser capture engine that archives every resource the browser receives during navigation. This is the CLI equivalent of Chrome's "Save All Resources" DevTools extension.

## When to use this

The user wants to capture/record/archive what a browser loads. They care about:
- Every resource the browser receives (JS, CSS, HTML, fonts, images, API responses, XHR)
- Resources served from cache that never hit the network
- Full request/response headers and metadata
- The actual file contents, organized by domain
- Inline data URIs extracted from CSS/HTML

They do NOT care about:
- What the page "says" or its text content
- Summarizing or interpreting the page
- Completing tasks on the page
- Scraping structured data

## How to use it

Run the capture engine:

```bash
NODE_PATH="${CLAUDE_PLUGIN_DATA}/node_modules" node "${CLAUDE_PLUGIN_ROOT}/scripts/capture.js" \
  --urls <url1> <url2> ... \
  --output ./browser-capture-output
```

To capture authenticated pages using cookies from the user's real browser:

```bash
NODE_PATH="${CLAUDE_PLUGIN_DATA}/node_modules" node "${CLAUDE_PLUGIN_ROOT}/scripts/capture.js" \
  --urls <url1> <url2> ... \
  --cookies-from chrome \
  --output ./browser-capture-output
```

Cookie flags:
- `--cookies-from <browser>` — import cookies from a real browser (chrome, brave, edge, chromium, arc, vivaldi, opera)
- `--cookie-domains <d1,d2>` — only import cookies for specific domains (comma-separated)
- `--cookie-profile <name>` — browser profile (default: `Default`)

The output is a domain-organized directory tree. Every resource gets a real file at its URL path. Resources where content couldn't be retrieved get a `No Content: {url}` marker file. A `_metadata.json` sidecar has the full request/response headers, status, timing, resource type, and cache status for every entry.

## Critical behavior

1. **The archive IS the deliverable.** Do not summarize, analyze, or interpret the captured content unless the user asks you to after the capture is complete.
2. **Capture everything by default.** Beautify, all domains, no-content markers, data URI extraction — all ON unless the user says otherwise.
3. **Your job during capture is navigation, not task completion.** The browser is an instrument for recording, not a tool for accomplishing tasks on the site. Navigate to the pages the user described so the capture has what it needs.
4. **After capture, report what was captured:** total files, size, domains hit, resource type breakdown. Then ask if the user wants to filter, grep, or analyze anything from the capture.
5. **Cookie import is opt-in.** If the user mentions needing to be logged in, authenticated, or access private pages, use `--cookies-from <browser>`. Ask which browser if unclear. Never import cookies unless the user indicates they need authentication.
6. **Cookie import is non-fatal.** If cookie import fails (browser not found, DB locked, decryption error), the capture continues without cookies. Report the failure but don't abort.
