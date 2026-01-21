---
name: theme-creation
description: This skill should be used when the user asks to "create a theme", "new theme", "create an omarchy theme", "make a theme from wallpaper", "theme from image", "extract palette from image", "generate colors.toml", "design a theme", "build theme", "theme workshop", "publish theme to github", "omarchy-theme-set", "customize colors", "theme colors", or mentions hellwal, tint, palette extraction, or omarchy theming. Covers the complete workflow: palette extraction with hellwal, colors.toml generation, theme testing, preview capture, and GitHub publishing.
version: 1.0.0
---

# Omarchy Theme Creation

Create Omarchy themes from wallpaper images using automated palette extraction with hellwal.

## Workshop Location

Develop themes in: `~/omarchy-theme-workshop/<theme-name>/`

**NEVER create themes directly in:**
- `~/.config/omarchy/themes/` (install destination only)
- `~/.local/share/omarchy/themes/` (read-only stock themes)

## Required Tools

### hellwal

Install via omarchy:
```bash
omarchy-pkg-aur-add hellwal
```

Extract palette:
```bash
hellwal -i <image> --json --check-contrast
```

Flags: `--json` (structured output), `--dark`/`--light` (force mode), `--check-contrast` (readability), `--neon-mode` (vibrant)

### tint

Location: `${CLAUDE_PLUGIN_ROOT}/bin/tint` (Claude Code sets this variable to the plugin's install directory)

Before use, verify the binary exists by running `${CLAUDE_PLUGIN_ROOT}/bin/tint --version`. If it fails, run `${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh`.

Recolor images to match palette:
```bash
${CLAUDE_PLUGIN_ROOT}/bin/tint -i <image> -t <theme-name>
```

## colors.toml Structure

Omarchy themes require 22 color slots:

| Slot | Purpose |
|------|---------|
| accent | Primary accent (buttons, links, focus) |
| cursor | Cursor color |
| foreground | Default text |
| background | Window/app background |
| selection_foreground | Selected text color |
| selection_background | Selection highlight |
| color0-7 | Base ANSI colors (black, red, green, yellow, blue, magenta, cyan, white) |
| color8-15 | Bright ANSI variants |

### Mapping hellwal Output

Map hellwal JSON to colors.toml (see `references/colors-toml-example.md` for detailed example):
- `background`, `foreground`, `color0-15` map directly
- Derive `accent` from color4 or color6 (see `references/colors-toml-example.md` for how to compare saturation)
- Derive `cursor` from foreground or color5
- Set `selection_foreground` = background, `selection_background` = accent

## Theme Directory Structure

```
omarchy-<name>-theme/
├── backgrounds/
│   ├── 1-primary.png
│   ├── 2-alternate.png
│   └── ...
├── colors.toml
├── preview.png
├── btop.theme        (optional)
├── icons.theme       (optional)
├── neovim.lua        (optional)
├── vscode.json       (optional)
└── waybar.css        (optional)
```

Number backgrounds (`1-name.png`, `2-name.png`) to set the cycle order. `omarchy-theme-bg-next` advances through them numerically, cycling back to 1 after the last (e.g., 1→2→3→1).

## Workflow

Follow these steps to create a complete theme:

### 1. Setup Workshop

```bash
mkdir -p ~/omarchy-theme-workshop/<name>/backgrounds
```

### 2. Acquire Background

Copy user-provided image to the backgrounds directory:
```bash
cp <user-image> ~/omarchy-theme-workshop/<name>/backgrounds/1-wallpaper.png
```

For random wallpapers, use the Minimalistic Wallpaper API (verify availability first):
```bash
# Test API availability
curl -sI "https://minimalistic-wallpaper.demolab.com/?random" | head -1

# If 200 OK, download wallpaper
curl -sL "https://minimalistic-wallpaper.demolab.com/?random" -o ~/omarchy-theme-workshop/<name>/backgrounds/1-wallpaper.png
```

If the API returns errors or times out, inform the user: "The random wallpaper API is unavailable. Please provide an image path or URL."

### 3. Extract Palette

```bash
hellwal -i ~/omarchy-theme-workshop/<name>/backgrounds/1-* --json --check-contrast
```

### 4. Generate colors.toml

Parse hellwal JSON output, derive accent/cursor/selection colors, write to `colors.toml`.

### 5. Test Theme

```bash
omarchy-theme-set ~/omarchy-theme-workshop/<name>
```

### 6. Capture Screenshot

```bash
grim ~/omarchy-theme-workshop/<name>/preview.png
```

With editing:
```bash
grim - | satty --filename - --output-filename ~/omarchy-theme-workshop/<name>/preview.png
```

### 7. Publish to GitHub

```bash
cd ~/omarchy-theme-workshop/<name>
git init
git add .
git commit -m "Initial theme: <name>"
gh repo create omarchy-<name>-theme --public --source=. --push
```

Install the newly published theme:
```bash
omarchy-theme-install "$(gh repo view --json url --jq .url)"
```

### 8. Register with Tint

Register the palette with tint for recoloring other images. See `references/hellwal-registration.md` for the `.hellwal` file format.

## Checkpoints

Pause for user review at:
1. After palette extraction - show colors
2. After colors.toml - show slot assignments
3. After theme test - confirm appearance
4. After screenshot - review preview.png
5. After GitHub push - provide install URL

## Additional Resources

### Reference Files

- **`references/colors-toml-example.md`** - Complete colors.toml example with slot mapping
- **`references/hellwal-registration.md`** - Tint palette registration format
