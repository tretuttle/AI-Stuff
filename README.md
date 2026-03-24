<!-- PROJECT SHIELDS -->
<div align="center">

[![GitHub Stars][stars-shield]][stars-url]
[![License: MIT][license-shield]][license-url]
[![GitHub Issues][issues-shield]][issues-url]

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

---

## Plugins

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

<div align="center">

<a href="https://claude.com/claude-code"><img src="assets/open-in-claude-code.svg" alt="Open in Claude Code" /></a>
&nbsp;&nbsp;
<img src="assets/works-on-my-machine.svg" alt="Works on My Machine" />
&nbsp;&nbsp;
<img src="assets/designed-in-ms-paint.svg" alt="Designed in MS Paint" />

</div>

---

## License

MIT

<!-- LINKS -->
[stars-shield]: https://img.shields.io/github/stars/tretuttle/AI-Stuff?style=social
[stars-url]: https://github.com/tretuttle/AI-Stuff/stargazers
[license-shield]: https://img.shields.io/badge/License-MIT-green.svg
[license-url]: https://github.com/tretuttle/AI-Stuff/blob/master/LICENSE
[issues-shield]: https://img.shields.io/github/issues/tretuttle/AI-Stuff
[issues-url]: https://github.com/tretuttle/AI-Stuff/issues
