---
description: Create a new Omarchy theme from wallpaper images
argument-hint: <name> [--image <path|url|random>] [--mode dark|light] [--vibe <description>]
allowed-tools: Bash, Read, Write, Edit, WebFetch
---

Create an Omarchy theme named $1.

## Setup

1. Verify hellwal installed:
   ```bash
   command -v hellwal || omarchy-pkg-aur-add hellwal
   ```

2. Create workshop:
   ```bash
   mkdir -p ~/omarchy-theme-workshop/$1/backgrounds
   ```

## Acquire Background

Parse remaining arguments for --image, --mode, --vibe flags.

If --image is "random" or not specified:
```bash
curl -sL "https://minimalistic-wallpaper.demolab.com/?random" -o ~/omarchy-theme-workshop/$1/backgrounds/1-wallpaper.png
```

If --image is a URL, download it. If a local path, copy it.

For multiple images, number them: 1-primary.png, 2-alternate.png, etc.

## Extract Palette

Run hellwal on the primary background:
```bash
hellwal -i ~/omarchy-theme-workshop/$1/backgrounds/1-*.png --json --check-contrast
```

Add --dark or --light flag if --mode was specified.

## CHECKPOINT: Palette Review

**STOP HERE.** Present the extracted colors:
- Show each color with its hex value
- Indicate detected mode (dark/light)
- Ask: "How does this palette look? Any colors to adjust?"

Wait for user feedback before continuing.

## Generate colors.toml

Map hellwal output to omarchy's 22-slot format:
- background, foreground, color0-15 from hellwal
- accent = color4 or color6 (pick more vibrant)
- cursor = foreground or color5
- selection_foreground = background
- selection_background = accent

If --vibe was provided, consider it when choosing accent/cursor.

Write to ~/omarchy-theme-workshop/$1/colors.toml

## CHECKPOINT: colors.toml Review

**STOP HERE.** Show the generated colors.toml with slot assignments.
Ask: "Does this mapping look right? Any slots to change?"

Wait for user feedback before continuing.

## CHECKPOINT: Test Theme

**STOP HERE.** Tell the user:
```
Theme files ready for testing. Run:
  omarchy-theme-set ~/omarchy-theme-workshop/$1

Check appearance across terminal, waybar, walker, window borders.
Let me know when ready to continue or if adjustments needed.
```

Wait for user confirmation before suggesting /theme-finalize.
