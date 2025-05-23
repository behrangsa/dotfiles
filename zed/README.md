# zed

Configuration and customization for the Zed editor.

## Description

The `zed` module provides a curated configuration for the Zed editor, optimizing it for development with:

- Custom font settings (Maple Mono NF)
- Enhanced UI/UX preferences
- GitHub Copilot integration
- Language-specific formatting rules
- VSCode-like keybindings
- TypeScript and Markdown formatting with Prettier
- Centered layout for better readability
- Optimized tab behavior and git integration

## Prerequisites

- Zed editor installed
- Maple Mono Nerd Font (optional, falls back to system fonts)
- Prettier (optional, for TypeScript/Markdown formatting)

## Installation

The module will be installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

This will create a symbolic link from `~/.config/zed/settings.json` to this module's `settings.json`.

## Features

### Font Configuration

- UI Font: Noto Sans with emoji fallback
- Buffer Font: Maple Mono NF with ligatures
- Customizable font sizes and weights
- Comfortable line height

### Editor Behavior

- Autosave after 5 seconds
- Copy on terminal select
- Active pane magnification
- All-line highlighting
- System-based theme switching
- Centered layout with customizable padding

### GitHub Copilot Integration

- Subtle prediction mode
- Disabled in sensitive files
- Configurable proxy settings
- Right-docked agent panel
- Default model: Gemini 2.5 Pro (via Copilot Chat)
- Inline assistant model: GPT-4.1 (via Copilot Chat)

### Language Support

- TypeScript/TSX formatting with Prettier
- Markdown formatting with Prettier
- LaTeX build configuration
- Import organization on format

### Privacy & Performance

- Telemetry disabled
- Optimized buffer settings
- Smart tab management
- Git status integration in tabs

## Customization

To modify settings, edit `settings.json` in this directory. The changes will be reflected in Zed after restarting the editor.

## Keybindings

Uses VSCode-like keybindings for familiarity, including:

- Cmd/Ctrl+P for file switching
- Cmd/Ctrl+Shift+P for command palette
- Standard editing shortcuts
- Terminal integration shortcuts

## Theme

Uses Ayu Dark theme by default, with system mode detection for automatic switching between light/dark variants.

## Notes

- Font features require Maple Mono Nerd Font for full functionality
- Some features require external tools (e.g., Prettier for formatting)
- GitHub authentication required for Copilot features
