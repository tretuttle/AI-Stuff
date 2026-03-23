# AI-Stuff

A collection of Claude Code plugins for AI-assisted workflows.

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add tretuttle/AI-Stuff
```

Then install individual plugins:

```
/plugin install omarchy-theme@ai-stuff
/plugin install browser-capture@ai-stuff
```

## Available Plugins

### omarchy-theme

Create Omarchy desktop themes from wallpaper images with automated palette extraction.

**Features:**
- Extract color palettes from wallpaper images using hellwal
- Recolor UI assets to match your wallpaper with tint
- Generate complete theme packages for Omarchy desktop
- Workshop-based workflow at `~/omarchy-theme-workshop/`

[View plugin details](./omarchy-theme/README.md)

### browser-capture

Complete browser resource capture using Playwright + Chrome DevTools Protocol. Archives every resource the browser receives during navigation into a domain-organized directory with full metadata.

**Features:**
- Capture all network traffic (XHR, fetch, scripts, CSS, fonts, images, API responses)
- Cached/static resources from the browser's resource tree
- Full request/response metadata (headers, status codes, timing, cache status)
- Domain-organized directory structure with actual files
- Post-capture analysis agent for filtering and searching

[View plugin details](./plugins/browser-capture/README.md)

### persona

Multi-persona code review orchestrator — get feedback from diverse expert perspectives.

**Features:**
- 15+ expert persona agents (Chris Coyier, DHH, and more)
- Orchestration skill to run multi-persona reviews
- Progress tracking via hooks
- Persistent memory for accumulated insights

```
/plugin install persona@ai-stuff
```

[View plugin details](./persona/README.md)

## License

MIT
