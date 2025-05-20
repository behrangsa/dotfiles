# 🧰 behrangsa's Dotfiles

This repository contains configuration files and utilities that form the
foundation of my Linux development environment.

## 📦 Modules

| Module       | Purpose                                        | Dependencies                |
| ------------ | ---------------------------------------------- | --------------------------- |
| **help**     | Expert terminal help system using OpenAI API   | Python, requests            |
| **openai**   | Command-line interface for OpenAI API          | Python, rich, pygments      |
| **npmrc**    | NPM configuration with security best practices | Node.js                     |
| **mkfav**    | Generate favicon.ico from images               | Bash, ImageMagick           |
| **memviz**   | Memory usage visualization (treemap)           | Python, psutil,             |
|              |                                                | matplotlib, squarify        |
| **imgsizes** | Image resizing utility                         | Python, ImageMagick         |
| **imgls**    | Terminal image grid display                    | Bash, Kitty terminal        |
| **imgtag**   | AI-powered image metadata tagging              | Python, Ollama, exiftool    |
| **git**      | Git configuration                              | Git                         |
| **emptybye** | Empty directory removal tool                   | Python 3                    |
| **conky**    | System monitoring dashboard                    | Conky                       |
| **thumbgen** | Thumbnail generation utility                   | Python, Pillow              |
| **zed**      | Zed editor configuration                       | Zed                         |
| **sqlite**   | SQLite database dump utility                   | Python, pandas              |
| **lmdumpb**  | LMDB database dump utility                     | Python, pandas, python-lmdb |

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

- Provides expert terminal help by leveraging the OpenAI API.
- Get assistance with commands for various tools like Vim, Bash, and Git.

```bash
# Get expert help on Vim commands
bu-help -s vim -p "How can I show line numbers in vim, persistently"

# Learn Bash file operations
bu-help -s bash -p "How do I find and replace text in multiple files"

# Get Git guidance
bu-help -s git -p "How to squash my last 3 commits"
```

### openai

- A command-line interface to interact with the OpenAI API.
- List models, manage configurations, and more.

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

- A utility to create multi-resolution `favicon.ico` files (16x16, 32x32, 48x48, 256x256) from a source image.
- Uses ImageMagick to perform the image conversion and bundling.

```bash
# Create favicon from an image
mkfav logo.png

# Custom output filename
mkfav image.png custom_favicon.ico

# Specify full paths
mkfav /path/to/image.jpg /path/to/output/favicon.ico
```

### memviz

- Visualizes memory usage as a treemap.
- Outputs an image and an optional CSV file of memory consumption.

```bash
# Usage
memviz --output ~/ram_usage.png --csv ~/ram_usage.csv
```

### imgsizes

- A utility for resizing images using ImageMagick.
- (Example usage to be added)

### imgtag

- AI-powered image tagging, metadata enrichment, and smart renaming utility.
- Uses Ollama's AI models to automatically generate descriptive filenames, meaningful descriptions, and relevant keywords.
- Embeds metadata into image files for better organization and can rename files based on content.
- Features batch processing, preview of suggestions, and safety measures against accidental overwrites.

```bash
# AI-powered image organization
imgtag ~/Pictures/001.jpg -w  # Analyze and write metadata
imgtag ~/Photos/ -f           # Batch process with force overwrite
```

### imgls

- Displays images from the current directory in a grid within the Kitty terminal.
- Supports customizable column counts and pagination.

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

### git

- Contains customized Git configurations for an optimized workflow.
- (Details of specific configurations can be found in the `git` module directory.)

### emptybye

- A utility to find and remove empty directories efficiently using a depth-first search.
- Handles nested empty directories and parent directories that become empty after child removal.
- Features a dry-run mode to preview changes, and options for symlink handling and verbose logging.

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

TODO.

### zed

- Configuration files for Zed editor
- Custom keybindings and themes
- Optimized for Python, JavaScript, and Markdown editing

### sqlite

- A command-line utility to export tables from an SQLite database to individual HTML files.
- Dumps all tables from a specified database, saving each as a separate HTML file.
- Allows specification of an output directory for the exported files.

```bash
# Export tables from 'mydatabase.db' to the current directory
bu-sqlite-dump --db mydatabase.db

# Export tables from 'mydatabase.db' to a directory named 'db_export'
bu-sqlite-dump --db mydatabase.db --output ./db_export
```

### lmdumpb

- A command-line utility to export data from an LMDB (Lightning Memory-Mapped Database) to an HTML file.
- Facilitates inspection and sharing of LMDB database contents.

```bash
# Export data from 'my_lmdb_data_dir' to an HTML file in the current directory
bu-lmdb-dump --db ./my_lmdb_data_dir

# Export data from 'my_lmdb_data_dir' to a directory named 'lmdb_export'
bu-lmdb-dump --db ./my_lmdb_data_dir --output ./lmdb_export
```

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
