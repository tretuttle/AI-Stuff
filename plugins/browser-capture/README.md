# browser-capture

Claude Code plugin for complete browser resource capture using Playwright + Chrome DevTools Protocol.

The CLI equivalent of Chrome's "Save All Resources" DevTools extension. Captures every resource the browser receives during navigation -- network traffic, cached assets, resource tree entries -- and writes them to a domain-organized directory with full metadata.

## Install

### From marketplace

```
# Add the marketplace (one-time)
/plugin marketplace add tretuttle/AI-Stuff

# Install the plugin
/plugin install browser-capture@ai-stuff
```

### Local development

```
claude --plugin-dir ./plugins/browser-capture
```

## Usage

### Slash command

```
/browser-capture:capture https://example.com https://example.com/page2
```

### Natural language

Or just describe what you want:

> Capture everything from the Claude Code plugin docs

The skill auto-triggers when it detects capture/archive/record intent -- no slash command needed.

## Available flags

- `--urls <url1> <url2> ...` -- URLs to navigate (required)
- `--output <dir>` -- output directory (default: `./browser-capture-output/`)
- `--no-beautify` -- skip JS/CSS/HTML beautification
- `--single-domain` -- only save resources from the primary domain
- `--skip-no-content` -- don't write marker files for unretrievable resources
- `--skip-data-uris` -- don't extract inline data URIs
- `--follow-links` -- follow sub-links on pages
- `--follow-depth <n>` -- max depth for link following (default: 1)

## What it captures

This is NOT a scraper or summarizer. It captures everything the browser receives:

- All network traffic (XHR, fetch, scripts, CSS, fonts, images, API responses)
- Cached/static resources from the browser's resource tree
- Full request/response headers, status codes, timing, cache status
- Resources organized by domain and URL path as actual files
- Inline data URIs extracted from CSS/HTML
- Marker files for resources that exist but whose content couldn't be retrieved

## Output structure

```
browser-capture-output/
├── _metadata.json
├── _summary.txt
├── example.com/
│   ├── index.html
│   └── assets/
│       ├── style.css
│       └── app.js
└── cdn.example.com/
    └── lib.js
```

- `_metadata.json` -- full request/response metadata for every resource (headers, status, timing, cache status, resource type)
- `_summary.txt` -- file counts by domain, type, and status
- Domain directories contain the actual captured files at their URL paths

## Post-capture analysis

After a capture completes, a built-in analysis agent can filter, grep, and summarize the results. Example prompts:

- "Show me all the API endpoints this page calls"
- "List all domains this page talks to"
- "Grep the JS files for config objects"
- "What XHR requests were made?"
- "Filter to just the fetch/xhr resources"

The analysis agent reads the `_metadata.json` sidecar and the captured files on disk. It can filter by resource type, domain, status code, cache status, or content pattern.

## Dependencies

Installed automatically on first run via SessionStart hook:

- **playwright** -- Headless Chromium for navigation and CDP session access
- **js-beautify** -- Beautifies captured JS/CSS/HTML for readability

No manual dependency installation required. The hook checks for missing dependencies at the start of every session and installs them to `${CLAUDE_PLUGIN_DATA}` if needed.
