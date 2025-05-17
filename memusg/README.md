# MemUSG - System Memory Usage Visualizer

A powerful tool for visualizing and analyzing system memory usage through interactive treemaps.

![Memory Usage Treemap Example](https://i.imgur.com/QpOeG8x.png)

## Overview

MemUSG creates detailed, interactive visualizations of your system's memory usage, showing which processes are consuming memory resources. The tool generates treemaps where each rectangle represents a process, with the size proportional to its memory footprint.

## Features

- 📊 **Visual Memory Analysis**: Generate treemap visualizations of memory usage
- 👥 **User Grouping**: Group processes by username for management perspective
- 📄 **Export Options**: Save data as CSV, JSON and PNG formats
- 🎨 **Customizable Visuals**: Multiple color schemes and display options
- 🔍 **Filtering**: Focus on specific processes by excluding others
- ⚙️ **Headless Support**: Run in non-GUI environments

## Installation

```bash
# Run the included installation script
./install.sh
```

The script will:
1. Check for required dependencies
2. Install them if needed (with your permission)
3. Create a symbolic link to make the command available

## Dependencies

- Python 3.6+
- psutil
- matplotlib
- squarify
- numpy

## Usage

### Basic Usage

```bash
# Generate and display a memory usage treemap
memusg

# Save the treemap to a specific file
memusg -o memory_usage.png
```

### Advanced Options

```bash
# Group processes by username with custom colors
memusg --group-by username --color-by-user

# Export detailed data to JSON and CSV
memusg --json memory_data.json --csv memory_data.csv

# Focus on the top memory consumers
memusg --top 30 --min-memory 50

# Exclude specific processes or users
memusg --exclude-pids 1234,5678 --exclude-users system,daemon

# Run in headless mode (e.g., on servers without GUI)
memusg --headless -o server_memory.png --no-display
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output path for the treemap image |
| `--csv` | Output path for CSV data export |
| `--json` | Output path for JSON data export |
| `--width` | Width of the output image in inches (default: 48) |
| `--height` | Height of the output image in inches (default: 30) |
| `--dpi` | DPI of the output image (default: 100) |
| `--min-memory` | Minimum memory threshold in MB (default: 1.0) |
| `--colormap` | Colormap for the visualization |
| `--no-display` | Don't attempt to display the visualization |
| `--no-csv` | Don't export data to CSV |
| `--no-json` | Don't export data to JSON |
| `--group-by` | Group processes by attribute (username, none) |
| `--color-by-user` | Color rectangles by username |
| `--exclude-pids` | Comma-separated list of PIDs to exclude |
| `--exclude-users` | Comma-separated list of usernames to exclude |
| `--top` | Show only top N processes by memory usage |
| `--headless` | Force headless mode (no GUI dependencies) |
| `-v, --verbose` | Enable verbose logging |

## Examples

### Basic Memory Analysis

```bash
# Generate a standard memory visualization
memusg
```

### Focus on Memory-Intensive Applications

```bash
# Show only processes using at least 100MB
memusg --min-memory 100 --top 20
```

### User-Based Analysis

```bash
# Group and color processes by user
memusg --group-by username --color-by-user --colormap Set1
```

### Non-Interactive Server Analysis

```bash
# Generate visualization on a headless server
memusg --headless --no-display -o /path/to/result.png
```

## License

This module is part of the dotfiles collection and follows the same licensing terms.