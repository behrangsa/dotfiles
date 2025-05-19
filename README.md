# 🧰 behrangsa's Dotfiles

> "Simplicity is a great virtue but it requires hard work to achieve it."
> &mdash; Edsger W. Dijkstra

This repository contains configuration files and utilities that form the
foundation of my Linux development environment.

## 📦 Modules

| Module       | Purpose                                        | Dependencies             |
| ------------ | ---------------------------------------------- | ------------------------ |
| **help**     | Expert terminal help system using OpenAI API   | Python, requests         |
| **openai**   | Command-line interface for OpenAI API          | Python, rich, pygments   |
| **npmrc**    | NPM configuration with security best practices | Node.js                  |
| **mkfav**    | Generate favicon.ico from images               | Bash, ImageMagick        |
| **memviz**   | Memory usage visualization (treemap)           | Python, psutil,          |
|              |                                                | matplotlib, squarify     |
| **imgsizes** | Image resizing utility                         | Python, ImageMagick      |
| **imgls**    | Terminal image grid display                    | Bash, Kitty terminal     |
| **imgtag**   | AI-powered image metadata tagging              | Python, Ollama, exiftool |
| **git**      | Git configuration                              | Git                      |
| **emptybye** | Empty directory removal tool                   | Python 3                 |
| **conky**    | System monitoring dashboard                    | Conky                    |
| **thumbgen** | Thumbnail generation utility                   | Python, Pillow           |
| **zed**      | Zed editor configuration                       | Zed                      |

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/behrangsa/dotfiles.git ~/.dotfiles

# Run installer
cd ~/.dotfiles
./install.sh
```

## 🧾 Module Details

### help

```bash
# Get expert help on Vim commands
bu-help -s vim -p "How can I show line numbers in vim, persistently"

# Learn Bash file operations
bu-help -s bash -p "How do I find and replace text in multiple files"

# Get Git guidance
bu-help -s git -p "How to squash my last 3 commits"
```

### openai

```bash
# List all available models
bu-openai ls models

# List models in a table format
bu-openai ls models --table

# Filter models containing 'gpt' sorted by creation date
bu-openai ls models --filter gpt --sort created --pretty-dates

# Configure your API key
bu-openai configure
```

### npmrc

- Security-focused configuration
- Strict version control with exact dependencies
- Optimized for slow network connections
- File permissions set to 600 for credentials

### mkfav

```bash
# Create favicon from an image
mkfav logo.png

# Custom output filename
mkfav image.png custom_favicon.ico

# Specify full paths
mkfav /path/to/image.jpg /path/to/output/favicon.ico
```

### memviz

```bash
# Usage
memviz --output ~/ram_usage.png --csv ~/ram_usage.csv
```

### imgtag

```bash
# AI-powered image organization
imgtag ~/Pictures/001.jpg -w  # Analyze and write metadata
imgtag ~/Photos/ -f           # Batch process with force overwrite
```

### imgls

```bash
# Display images in a 3-column grid (default)
imgls

# Display images in 4 columns with custom spacing
imgls 4

# Navigate through paginated image display
# Press any key to go to next page
# Press 'q' to quit
imgls 2  # 2-column display with pagination
```

### emptybye

```bash
# Dry run first
emptybye ~/Downloads/unsorted --dry-run

# Remove empty directories
emptybye ~/Downloads/unsorted
```

## 📊 Conky Dashboard

- Real-time system monitoring
- Temperature, CPU, memory, and disk usage
- Custom color scheme with transparency support

### thumbgen

```bash
# Generate thumbnails for images
bu-thumbgen ~/Pictures/album
```

### zed

- Configuration files for Zed editor
- Custom keybindings and themes
- Optimized for Python, JavaScript, and Markdown editing

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
