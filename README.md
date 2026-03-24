# AI-Stuff

A collection of Claude Code plugins for AI-assisted workflows.

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add tretuttle/AI-Stuff
```

Then install individual plugins:

```
/plugin install persona@ai-stuff
/plugin install omarchy-theme@ai-stuff
/plugin install browser-capture@ai-stuff
```

## Available Plugins

### persona

Multi-persona code review and interactive dev chat. 14 expert personas — ThePrimeagen, DHH, Rich Harris, Dan Abramov, and more — each applying their principles to your codebase, in your language, with your framework.

**Features:**
- Parallel multi-persona code review with synthesis, deduplication, and confidence scoring
- Interactive persona chat — channel any developer's voice with full tool access
- Guided workflow (`/persona:run`) plus power-user shortcuts (`/persona:review`, `/persona:call`)
- Principle-based, stack-agnostic — personas apply transferable beliefs to any codebase
- Always opinionated — full intensity by default, real catchphrases, authentic voice
- Project memory — personas accumulate insights across sessions

```
/plugin install persona@ai-stuff
```

[View plugin details](./persona/README.md)

### omarchy-theme

Create Omarchy desktop themes from wallpaper images with automated palette extraction.

**Features:**
- Extract color palettes from wallpaper images using hellwal
- Recolor UI assets to match your wallpaper with tint
- Generate complete theme packages for Omarchy desktop
- Workshop-based workflow at `~/omarchy-theme-workshop/`

```
/plugin install omarchy-theme@ai-stuff
```

[View plugin details](./omarchy-theme/README.md)

### browser-capture

Complete browser resource capture using Playwright + Chrome DevTools Protocol. Archives every resource the browser receives during navigation into a domain-organized directory with full metadata.

**Features:**
- Capture all network traffic (XHR, fetch, scripts, CSS, fonts, images, API responses)
- Cached/static resources from the browser's resource tree
- Full request/response metadata (headers, status codes, timing, cache status)
- Domain-organized directory structure with actual files
- Post-capture analysis agent for filtering and searching

```
/plugin install browser-capture@ai-stuff
```

[View plugin details](./plugins/browser-capture/README.md)

## License

MIT
