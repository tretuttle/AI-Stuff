# colors.toml Complete Example

Reference example based on catppuccin theme:

```toml
# Core colors
accent = "#89b4fa"
cursor = "#f5e0dc"
foreground = "#cdd6f4"
background = "#1e1e2e"
selection_foreground = "#1e1e2e"
selection_background = "#f5e0dc"

# Terminal palette (ANSI colors)
color0 = "#45475a"   # Black
color1 = "#f38ba8"   # Red
color2 = "#a6e3a1"   # Green
color3 = "#f9e2af"   # Yellow
color4 = "#89b4fa"   # Blue
color5 = "#f5c2e7"   # Magenta
color6 = "#94e2d5"   # Cyan
color7 = "#bac2de"   # White
color8 = "#585b70"   # Bright Black
color9 = "#f38ba8"   # Bright Red
color10 = "#a6e3a1"  # Bright Green
color11 = "#f9e2af"  # Bright Yellow
color12 = "#89b4fa"  # Bright Blue
color13 = "#f5c2e7"  # Bright Magenta
color14 = "#94e2d5"  # Bright Cyan
color15 = "#a6adc8"  # Bright White
```

## Color Slot Usage

| Slot | Terminal Use | UI Use |
|------|--------------|--------|
| color0 | Black text/bg | Subtle backgrounds |
| color1 | Errors | Destructive actions |
| color2 | Success | Positive indicators |
| color3 | Warnings | Caution indicators |
| color4 | Info | Links, focus states |
| color5 | Special | Highlights |
| color6 | Strings | Paths, URLs |
| color7 | Secondary text | Muted content |
| color8-15 | Bright variants | Emphasis versions |

## hellwal JSON to colors.toml Mapping

hellwal outputs:
```json
{
  "wallpaper": "/path/to/image.png",
  "background": "#1e1e2e",
  "foreground": "#cdd6f4",
  "color0": "#45475a",
  "color1": "#f38ba8",
  "color2": "#a6e3a1",
  "color3": "#f9e2af",
  "color4": "#89b4fa",
  "color5": "#f5c2e7",
  "color6": "#94e2d5",
  "color7": "#bac2de",
  "color8": "#585b70",
  "color9": "#f38ba8",
  "color10": "#a6e3a1",
  "color11": "#f9e2af",
  "color12": "#89b4fa",
  "color13": "#f5c2e7",
  "color14": "#94e2d5",
  "color15": "#a6adc8"
}
```

Derive additional slots:
- `accent` = color4 (blue) or color6 (cyan) - pick whichever has higher saturation (more vivid, less gray). To compare programmatically, convert hex to HSL and compare S (saturation) values; higher S = more vibrant. Visually, the more "colorful" option is usually correct.
- `cursor` = foreground or color5
- `selection_foreground` = background (for contrast)
- `selection_background` = accent
