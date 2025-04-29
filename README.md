# 🧰 behrangsa's Dotfiles

> "Simplicity is a great virtue but it requires hard work to achieve it."
> &mdash; Edsger W. Dijkstra

This repository contains configuration files and utilities that form the
foundation of my Linux development environment.

## 📦 Modules

| Module       | Purpose                                        | Dependencies             |
| ------------ | ---------------------------------------------- | ------------------------ |
| **npmrc**    | NPM configuration with security best practices | Node.js                  |
| **mkfav**    | Generate favicon.ico from images               | Bash, ImageMagick        |
| **memusg**   | Memory usage visualization (treemap)           | Python, psutil,          |
|              |                                                | matplotlib, squarify     |
| **imgsizes** | Image resizing utility                         | Python, ImageMagick      |
| **imgfname** | AI-powered image metadata tagging              | Python, Ollama, exiftool |
| **git**      | Git configuration                              | Git                      |
| **emptybye** | Empty directory removal tool                   | Python 3                 |
| **conky**    | System monitoring dashboard                    | Conky                    |

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/behrangsa/dotfiles.git ~/.dotfiles

# Run installer
cd ~/.dotfiles
./install.sh
```

## 🧾 Module Details

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

### memusg

```bash
# Usage
memusg --output ~/ram_usage.png --csv ~/ram_usage.csv
```

### imgfname

```bash4
# AI-powered image organization
imgfname ~/Pictures/001.jpg -w  # Analyze and write metadata
imgfname ~/Photos/ -f           # Batch process with force overwrite
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

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
