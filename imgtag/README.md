# imgtag

AI-powered image tagging, metadata enrichment, and smart renaming utility.

## Overview

`imgtag` analyzes images using Ollama's AI models to automatically:

1. Generate descriptive filenames based on image content
2. Create meaningful descriptions for each image
3. Extract relevant keywords/tags from the image
4. Write metadata to image files for better organization
5. Rename files based on their content

## Features

- 🖼️ AI-powered image content analysis
- 📝 Automatic metadata generation and embedding
- 🏷️ Smart tagging with relevant keywords 
- 🔤 Intelligent filename suggestions
- 📁 Batch processing for entire directories
- 🔍 Preview suggestions before applying changes
- 🛡️ Safety measures to prevent accidental overwrites

## Installation

```bash
./install.sh
```

This will:
- Install the script to your `~/.local/bin/` directory
- Make the command available in your terminal as `imgtag`

## Dependencies

- [Ollama](https://ollama.ai/) - Local AI model runner
- [ExifTool](https://exiftool.org/) - For reading/writing image metadata
- Python 3.6+ with packages:
  - PIL/Pillow (image processing)
  - argparse, base64, os, re, sys (standard libraries)

## Usage

### Basic Usage

```bash
# Analyze a single image
imgtag path/to/image.jpg

# Process an entire directory of images
imgtag path/to/image/directory
```

### Writing Changes

```bash
# Prompt before writing metadata and renaming
imgtag -w path/to/image.jpg

# Force metadata writing and renaming without confirmation
imgtag -f path/to/image.jpg
```

## Supported Image Formats

JPEG, PNG, TIFF, WebP, HEIC/HEIF, AVIF, and many RAW formats (DNG, CR2, NEF, etc.)

## Options

```
-w, --write  : Write metadata and rename file(s) with confirmation
-f, --force  : Force write changes without confirmation (use with caution!)
```

## License

This module is part of the dotfiles collection and follows the same licensing terms.