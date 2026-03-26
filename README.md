<!-- PROJECT SHIELDS -->
<div align="center">

<img src="assets/works-on-my-machine.svg" alt="Works on My Machine" height="28" />
&nbsp;&nbsp;
<img src="assets/designed-in-ms-paint.svg" alt="Designed in MS Paint" height="28" />

</div>

<div align="center">

# AI-Stuff

**A Claude Code plugin marketplace by [tretuttle](https://github.com/tretuttle)**

</div>

---

## Install

```
/plugin marketplace add tretuttle/AI-Stuff
```

Then pick what you want:

```
/plugin install persona@ai-stuff
/plugin install omarchy-theme@ai-stuff
/plugin install browser-capture@ai-stuff
```

For Codex-only skills, use the package README in this repo instead of `/plugin install`.

---

## Plugins

### codex-session-export

> Saved session discovery and transcript export for Codex CLI. Lists saved Codex sessions, shows session IDs with friendly labels, and exports any session to `.jsonl` and readable `.txt` without touching the original resumable session.

- Finds saved Codex sessions from `~/.codex/sessions`
- Surfaces session UUIDs with practical resume-style labels
- Exports raw `.jsonl` and readable `.txt`
- Keeps the original session intact so `codex resume <SESSION_ID>` still works
- Includes copy and symlink install instructions for Codex

Codex install details:

```bash
cp -R ~/AI-Stuff/codex-session-export ~/.codex/skills/
```

[View details &#8594;](./codex-session-export/README.md)

---

### persona

> Multi-persona code review and interactive dev chat. 14 expert personas — ThePrimeagen, DHH, Rich Harris, Dan Abramov, and more — each applying their principles to YOUR codebase, in YOUR language, with YOUR framework.

- Parallel multi-persona review with synthesis, deduplication, and confidence scoring
- Interactive persona chat — channel any developer's voice with full tool access
- Guided workflow (`/persona:run`) plus power-user shortcuts (`/persona:review`, `/persona:call`)
- Principle-based and stack-agnostic — personas apply transferable beliefs to any codebase
- Always opinionated — full intensity, real catchphrases, authentic voice

```
/plugin install persona@ai-stuff
```

[View details &#8594;](./persona/README.md)

---

### omarchy-theme

> Desktop theme generator for Omarchy. Pick a wallpaper, get a complete theme — palette, colors.toml, preview screenshot, GitHub repo — in one conversation.

- Wallpaper to theme in one command with guided checkpoints
- Natural language — "Make me a dark theme from this forest wallpaper"
- 22-slot colors.toml generation with live preview and testing
- Safe by design — workshop directory, never touches system configs
- One-click GitHub publishing with install URL

```
/plugin install omarchy-theme@ai-stuff
```

> [!NOTE]
> Requires [Omarchy](https://github.com/nicholasgasior/omarchy) desktop environment.

[View details &#8594;](./omarchy-theme/README.md)

---

### browser-capture

> Complete browser resource capture using Playwright + Chrome DevTools Protocol. The CLI equivalent of Chrome's "Save All Resources" — every resource the browser receives, organized by domain, with full metadata.

- All network traffic — XHR, fetch, scripts, CSS, fonts, images, API responses
- Full request/response metadata (headers, status codes, timing, cache status)
- Domain-organized directory structure with actual files
- Authenticated captures — import cookies from Chrome, Brave, Edge, Arc, Vivaldi, Opera
- Post-capture analysis agent for filtering, grepping, and searching results
- Health diagnostics, output sanitization, and auto-update checking
- Zero setup — dependencies and Chromium install automatically with launch verification

```
/plugin install browser-capture@ai-stuff
```

[View details &#8594;](./plugins/browser-capture/README.md)

---

## License

MIT
