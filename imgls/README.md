# imgls

A terminal utility that displays images in a grid layout with pagination.

## Description

The `imgls` utility displays images in a terminal grid with an adjustable number of columns, automatic pagination, and truncated filenames. It's perfect for quickly browsing image directories in terminal environments that support kitty's image protocol.

Features:
- Grid display with configurable columns
- Automatic pagination
- Smart filename truncation
- Support for multiple image formats (jpg, jpeg, png, gif, webp, avif)
- Error handling with options to skip or quit
- Clean terminal restore on exit

## Prerequisites

- Kitty terminal emulator
- `tput` command (usually part of `ncurses`)

## Installation

The module will be installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

This will install the `imgls.sh` script to `~/.local/bin/imgls`.

## Usage

```bash
imgls [COLUMNS]
```

### Arguments

- `COLUMNS`: (Optional) Number of columns to display (default: 3)

### Examples

```bash
# Display images in 3 columns (default)
imgls

# Display images in 4 columns
imgls 4

# Display images in 2 columns
imgls 2
```

## Key Features

- **Grid Layout**: Images are displayed in a configurable grid with proper spacing
- **Adaptive Display**: Automatically adjusts to terminal dimensions
- **Smart Pagination**: Pages through images when they exceed screen space
- **Filename Display**: Shows truncated filenames below images with ellipsis
- **Format Support**: Handles common image formats (jpg, jpeg, png, gif, webp, avif)
- **Error Handling**: Gracefully handles display failures with continue/quit options
- **Clean Exit**: Restores terminal state on exit or interrupt

## Technical Details

The script uses:
- Terminal dimensions to calculate optimal image placement
- Kitty's image protocol for image rendering
- Unicode ellipsis for filename truncation
- ANSI escape sequences for cursor positioning
- Trap handlers for clean exit

## Notes

- Works only in terminals that support the Kitty image protocol
- Terminal must be able to support image display
- Screen size affects the number of images displayed per page
- Each image is scaled to maintain visibility in the grid