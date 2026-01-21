# Hellwal Theme Registration

Register theme palettes with tint to recolor additional images using the theme's colors.

## File Location

```
~/.config/hellwal/themes/<theme-name>.hellwal
```

## Format

The `.hellwal` file uses a placeholder syntax:

```
%% color0  = #161616 %%
%% color1  = #be4b4b %%
%% color2  = #5f9e65 %%
%% color3  = #c9a44b %%
%% color4  = #4b7bbe %%
%% color5  = #9e5f8e %%
%% color6  = #4b9e9e %%
%% color7  = #c8c8c8 %%
%% color8  = #404040 %%
%% color9  = #d46a6a %%
%% color10 = #7ec484 %%
%% color11 = #e0c06a %%
%% color12 = #6a9ed4 %%
%% color13 = #c47eb0 %%
%% color14 = #6ac4c4 %%
%% color15 = #e8e8e8 %%
%% background = #0a0a0a %%
%% foreground = #e0e0e0 %%
```

## Generation

Parse the theme's `colors.toml` and write each color in the `%% name = #value %%` format.

## Usage

After registration, recolor images with:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/tint -i <image> -t <theme-name>
```
