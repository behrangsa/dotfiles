# mkfav

A utility to create favicon.ico files from image files using ImageMagick.

## Description

The `mkfav` utility creates a multi-resolution favicon.ico file from an input image. 
The favicon will contain the following resolutions:
- 16x16
- 32x32
- 48x48
- 256x256

This is useful for web development where you need to quickly generate a favicon from an existing logo or image.

## Prerequisites

- ImageMagick must be installed on your system

## Installation

The module will be installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

This will install the `mkfav.sh` script to `~/.local/bin/mkfav`.

## Usage

```bash
mkfav [OPTIONS] INPUT_FILE [OUTPUT_FILE]
```

### Options

- `-h`, `--help`: Show help message and exit

### Arguments

- `INPUT_FILE`: Path to the input image file
- `OUTPUT_FILE`: (Optional) Path to the output favicon file (default: `favicon.ico` in current directory)

### Examples

```bash
# Create favicon.ico from logo.png in the current directory
mkfav logo.png

# Create custom_favicon.ico from logo.png
mkfav logo.png custom_favicon.ico

# Specify full paths
mkfav /path/to/image.jpg /path/to/output/favicon.ico
```

## How It Works

The script uses ImageMagick's `convert` command to create multiple resolutions of the input image and combine them into a single .ico file.

The actual command used is:

```bash
convert input.png \
    \( -clone 0 -resize 16x16! \) \
    \( -clone 0 -resize 32x32! \) \
    \( -clone 0 -resize 48x48! \) \
    \( -clone 0 -resize 256x256! \) \
    -delete 0 \
    favicon.ico
```