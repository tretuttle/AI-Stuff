---
description: Finalize theme, capture screenshot, publish to GitHub
argument-hint: <name> [--skip-screenshot]
allowed-tools: Bash, Read, Write, Edit
---

Finalize the Omarchy theme named $1.

## Validate Theme

Check workshop exists and has required files:
```bash
ls ~/omarchy-theme-workshop/$1/
ls ~/omarchy-theme-workshop/$1/backgrounds/
cat ~/omarchy-theme-workshop/$1/colors.toml
```

Verify colors.toml has all 22 slots and backgrounds/ has at least one image.

## Capture Screenshot

Unless --skip-screenshot was specified:

1. Ensure theme is applied:
   ```bash
   omarchy-theme-set ~/omarchy-theme-workshop/$1
   ```

2. **Preserve user's current workspace.** Do NOT close any windows the user has open.

3. **Set up showcase windows** on an empty workspace. Open apps that demonstrate the theme:
   - Terminal with neofetch or fastfetch running
   - File manager (thunar)
   - A second terminal showing code or config

   Use Hyprland dispatch to open on a fresh workspace:
   ```bash
   # Move to empty workspace
   hyprctl dispatch workspace 9

   # Open showcase apps (they inherit theme colors)
   kitty -e fastfetch &
   sleep 0.5
   thunar ~/omarchy-theme-workshop/$1 &
   sleep 0.5
   kitty &
   sleep 0.5

   # Tile windows nicely (master-stack layout)
   hyprctl dispatch layoutmsg orientationcycle
   ```

4. **CHECKPOINT: Arrange Windows**

   **STOP HERE.** Tell the user:
   ```
   I've opened showcase windows on workspace 9. Please:
   1. Arrange/resize windows as desired for the preview
   2. Optionally open additional apps (browser, code editor)
   3. Let me know when ready to capture
   ```

   Wait for user confirmation.

5. Capture screenshot:
   ```bash
   grim ~/omarchy-theme-workshop/$1/preview.png
   ```

   Or with editing via satty:
   ```bash
   grim - | satty --filename - --output-filename ~/omarchy-theme-workshop/$1/preview.png
   ```

6. **Return user to original workspace:**
   ```bash
   hyprctl dispatch workspace previous
   ```

## CHECKPOINT: Screenshot Review

**STOP HERE.** Show the preview path and ask:
"Screenshot saved to ~/omarchy-theme-workshop/$1/preview.png. Re-capture or proceed to publishing?"

Wait for user confirmation.

## Publish to GitHub

1. Initialize git repo:
   ```bash
   cd ~/omarchy-theme-workshop/$1
   git init
   git add .
   git commit -m "Initial theme: $1"
   ```

2. Create GitHub repo and push:
   ```bash
   gh repo create omarchy-$1-theme --public --source=. --push
   ```

3. Get repo URL:
   ```bash
   gh repo view --json url -q .url
   ```

## CHECKPOINT: Publish Complete

**STOP HERE.** Tell the user:
```
Theme published!

Install URL:
  omarchy-theme-install <repo-url>

Share this URL for others to install your theme.
```

## Register with Tint

1. Create hellwal themes directory:
   ```bash
   mkdir -p ~/.config/hellwal/themes
   ```

2. Generate .hellwal file from colors.toml:
   Parse colors.toml and write to ~/.config/hellwal/themes/$1.hellwal in format:
   ```
   %% color0  = #... %%
   %% color1  = #... %%
   ...
   %% background = #... %%
   %% foreground = #... %%
   ```

3. Confirm:
   ```
   Palette registered with tint. Recolor other images:
     ${CLAUDE_PLUGIN_ROOT}/bin/tint -i <image> -t $1
   ```

## Complete

The theme remains in `~/omarchy-theme-workshop/$1/` for future edits.
