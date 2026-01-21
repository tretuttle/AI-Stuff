# omarchy-theme

A Claude Code plugin for creating Omarchy desktop themes from wallpaper images.

## Features

- **Palette extraction** from wallpaper images using hellwal
- **22-slot colors.toml** generation for Omarchy theming
- **Multiple wallpaper** support per theme
- **Screenshot capture** with grim for preview.png
- **GitHub publishing** for easy sharing
- **Tint registration** for image recoloring

## Installation

**Via marketplace (recommended):**
```
/plugin marketplace add tretuttle/AI-Stuff
/plugin install omarchy-theme@ai-stuff
```

**Or clone directly:**
```bash
git clone https://github.com/tretuttle/AI-Stuff ~/.claude/plugins/local/AI-Stuff
```

Then run setup to install dependencies:
```bash
~/.claude/plugins/local/AI-Stuff/omarchy-theme/scripts/setup.sh
```

## Usage

### Create a new theme

```
/theme-create <name> [--image <path|url|random>] [--mode dark|light] [--vibe <description>]
```

**Examples:**
```
/theme-create midnight-forest --image ~/wallpapers/forest.png
/theme-create ocean-breeze --image random --mode dark
/theme-create sunset-glow --image <url-to-image> --vibe warm
```

### Finalize and publish

```
/theme-finalize <name> [--skip-screenshot]
```

This captures a screenshot, publishes to GitHub, and provides an install URL.

### Natural language (auto-triggered)

The `theme-generator` agent automatically activates when you describe what you want:

```
"Create a theme called midnight-forest from this wallpaper"
"Make me a new omarchy theme with a random minimalist wallpaper"
"Extract a color palette from this image for my desktop"
```

## Workflow

The plugin guides you through theme creation with checkpoints:

1. **Palette extraction** - Review extracted colors from wallpaper
2. **colors.toml generation** - Review slot assignments
3. **Theme testing** - Test with `omarchy-theme-set`
4. **Screenshot setup** - Opens showcase apps (terminal, file manager) on a fresh workspace without closing your existing windows
5. **Screenshot capture** - Arrange windows, then capture preview.png
6. **GitHub publishing** - Get install URL to share

## Safety

- All work happens in `~/omarchy-theme-workshop/<name>/`
- Never writes directly to `~/.config/omarchy/themes/`
- Install only via GitHub + `omarchy-theme-install`

## Hooks Behavior

This plugin registers two hooks:

- **SessionStart**: Checks for missing dependencies (hellwal, grim, gh) at the start of every Claude Code session. This adds minimal overhead (~10ms) and ensures you're notified of missing tools early.
- **PreToolUse**: Blocks any Write/Edit operations to system theme directories, enforcing the workshop pattern.

## Screenshot Workspace

During `/theme-finalize`, the plugin opens showcase windows on **workspace 9** to capture a preview screenshot. This assumes workspace 9 is available. Your existing windows on other workspaces are preserved and you're returned to your original workspace after capture.

## Dependencies

**Automatically installed by setup.sh:**
- **hellwal** - Palette extraction (installed via `omarchy-pkg-aur-add`)
- **tint** - Image recoloring (bundled binary downloaded to plugin's bin/)

**Expected on Omarchy (no action needed):**
- **grim** - Screenshot capture
- **gh** - GitHub CLI for publishing
- **kitty** - Terminal (or your configured terminal)
- **thunar** - File manager

## Optional: Auto-approve Commands

To skip confirmation prompts for theme commands, add to your project's `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(omarchy-theme-set:*)",
      "Bash(hellwal:*)",
      "Bash(grim:*)",
      "Bash(gh repo create:*)"
    ]
  }
}
```

## License

MIT
