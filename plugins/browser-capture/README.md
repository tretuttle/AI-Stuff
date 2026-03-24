<!-- PROJECT SHIELDS -->
<div align="center">

[![Claude Code Plugin][claude-shield]][claude-url]
[![License: MIT][license-shield]][license-url]
[![GitHub Stars][stars-shield]][stars-url]

</div>

<div align="center">

# browser-capture

**Complete browser resource capture for [Claude Code](https://claude.com/claude-code)**

The CLI equivalent of Chrome's "Save All Resources" DevTools extension. Captures every resource the browser receives during navigation and writes them to a domain-organized directory with full metadata.

</div>

---

## Why

You want to know exactly what a website loads — every script, stylesheet, font, API call, image, and cached asset. Not a scrape of the visible HTML. Not a summary. The actual files the browser receives, with full request/response metadata, organized by domain.

This is the tool for reverse engineering, security auditing, endpoint discovery, and building offline archives of what a browser actually sees.

## Features

- **Everything the browser receives** — network traffic (XHR, fetch, scripts, CSS, fonts, images, API responses), cached assets from the resource tree, inline data URIs
- **Full metadata** — request/response headers, status codes, timing, cache status for every resource
- **Domain-organized output** — files written to their URL paths under domain directories, exactly mirroring the site structure
- **Beautification** — captured JS/CSS/HTML is beautified for readability by default
- **Post-capture analysis** — built-in agent for filtering, grepping, and summarizing results after capture
- **Natural language** — "Capture everything from the Claude Code plugin docs" just works
- **Zero setup** — dependencies install automatically on first run

---

## Getting Started

### Install

```
/plugin marketplace add tretuttle/AI-Stuff
/plugin install browser-capture@ai-stuff
```

Dependencies (Playwright, js-beautify) are installed automatically via SessionStart hook.

### First Capture

```
/browser-capture:capture https://example.com
```

Or just describe what you want:

```
"Capture everything from the Claude Code plugin docs"
```

The skill auto-triggers when it detects capture/archive/record intent.

---

## Usage

```
/browser-capture:capture <urls> [flags]
```

| Flag | Description |
|------|-------------|
| `--urls <url1> <url2>` | URLs to navigate (required) |
| `--output <dir>` | Output directory (default: `./browser-capture-output/`) |
| `--no-beautify` | Skip JS/CSS/HTML beautification |
| `--single-domain` | Only save resources from the primary domain |
| `--skip-no-content` | Don't write marker files for unretrievable resources |
| `--skip-data-uris` | Don't extract inline data URIs |
| `--follow-links` | Follow sub-links on pages |
| `--follow-depth <n>` | Max depth for link following (default: 1) |

---

## What It Captures

> [!NOTE]
> This is NOT a scraper or summarizer. It captures **everything** the browser receives during navigation.

- All network traffic — XHR, fetch, scripts, CSS, fonts, images, API responses
- Cached/static resources from the browser's resource tree
- Full request/response headers, status codes, timing, cache status
- Resources organized by domain and URL path as actual files
- Inline data URIs extracted from CSS/HTML
- Marker files for resources that exist but whose content couldn't be retrieved

## Output Structure

```
browser-capture-output/
├── _metadata.json          # Full metadata for every resource
├── _summary.txt            # File counts by domain, type, status
├── example.com/
│   ├── index.html
│   └── assets/
│       ├── style.css
│       └── app.js
└── cdn.example.com/
    └── lib.js
```

| File | Purpose |
|------|---------|
| `_metadata.json` | Headers, status, timing, cache status, resource type for every captured resource |
| `_summary.txt` | Counts by domain, type, and status at a glance |
| Domain directories | Actual files at their URL paths |

---

## Post-Capture Analysis

After a capture completes, a built-in analysis agent can filter, grep, and summarize results.

> [!TIP]
> The agent reads `_metadata.json` and the captured files on disk. Ask it anything about the capture:
>
> ```
> "Show me all the API endpoints this page calls"
> "List all domains this page talks to"
> "Grep the JS files for config objects"
> "What XHR requests were made?"
> "Filter to just the fetch/xhr resources"
> ```

The agent can filter by resource type, domain, status code, cache status, or content pattern.

---

<details>
<summary><strong>Dependencies</strong></summary>

Installed automatically on first run via SessionStart hook:

- **playwright** — Headless Chromium for navigation and CDP session access
- **js-beautify** — Beautifies captured JS/CSS/HTML for readability

No manual dependency installation required.

</details>

## License

MIT

<!-- LINKS -->
[claude-shield]: https://img.shields.io/badge/Claude_Code-Plugin-blueviolet?logo=anthropic&logoColor=white
[claude-url]: https://claude.com/claude-code
[license-shield]: https://img.shields.io/badge/License-MIT-green.svg
[license-url]: https://github.com/tretuttle/AI-Stuff/blob/master/LICENSE
[stars-shield]: https://img.shields.io/github/stars/tretuttle/AI-Stuff?style=social
[stars-url]: https://github.com/tretuttle/AI-Stuff/stargazers
