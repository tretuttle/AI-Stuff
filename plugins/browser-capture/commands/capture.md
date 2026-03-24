---
description: Capture all browser resources from one or more URLs using Playwright+CDP. Produces a domain-organized directory of every resource the browser receives — network traffic, cached assets, resource tree entries — with full request/response metadata, beautified JS/CSS/HTML, and extracted data URIs.
---

# Browser Resource Capture

Run the Playwright+CDP capture engine against the specified URLs.

## Usage

The engine requires dependencies installed in `${CLAUDE_PLUGIN_DATA}`. Set NODE_PATH as a safety net (capture.js also self-resolves at startup):

```bash
NODE_PATH="${CLAUDE_PLUGIN_DATA}/node_modules" node "${CLAUDE_PLUGIN_ROOT}/scripts/capture.js" \
  --urls $ARGUMENTS \
  --output ./browser-capture-output
```

## Available flags

- `--urls <url1> <url2> ...` — URLs to navigate (required)
- `--output <dir>` — output directory (default: `./browser-capture-output/`)
- `--no-beautify` — skip JS/CSS/HTML beautification
- `--single-domain` — only save resources from the primary domain
- `--skip-no-content` — don't write marker files for unretrievable resources
- `--skip-data-uris` — don't extract inline data URIs
- `--follow-links` — follow sub-links on pages (useful for GitHub repos, SPAs)
- `--follow-depth <n>` — max depth for link following (default: 1)
- `--cookies-from <browser>` — import cookies from a real browser before capture (e.g. `chrome`, `brave`, `edge`, `chromium`, `arc`, `vivaldi`, `opera`). Enables capturing authenticated/logged-in pages.
- `--cookie-domains <d1,d2>` — comma-separated domains to import cookies for (default: all cookies from the browser)
- `--cookie-profile <name>` — browser profile to use (default: `Default`)

## Output structure

    browser-capture-output/
    +-- _metadata.json          # full request/response metadata for every resource
    +-- _summary.txt            # file counts by domain, type, status
    +-- _DataURI/               # extracted inline data URIs (if any)
    +-- example.com/
    |   +-- index.html
    |   +-- assets/
    |   |   +-- style.css
    |   |   +-- app.js
    |   +-- api/
    |       +-- data.json
    +-- cdn.example.com/
        +-- lib.js

## What this captures

This is NOT a scraper or summarizer. It captures everything the browser receives:
- All network traffic (XHR, fetch, scripts, stylesheets, fonts, images)
- Cached/static resources from the browser's resource tree (things that never hit the network)
- Full request/response headers, status codes, timing, cache status
- Resources organized by domain and URL path as actual files
- Marker files for resources that exist but whose content couldn't be retrieved

The deliverable is the archive, not a summary of what the page said.
