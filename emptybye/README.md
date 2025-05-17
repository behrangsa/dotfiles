# EmptyBye

A utility to find and remove empty directories efficiently.

## Overview

EmptyBye performs a depth-first search on a given directory to identify and remove empty directories. A directory is considered empty if it contains no files and no non-empty subdirectories.

The tool is designed to efficiently clean up file systems by removing unneeded empty directory structures, starting from the deepest levels and working upward.

## Features

- **Depth-First Approach**: Processes deepest directories first to properly handle nested empty directories
- **Safe Removal**: Verifies directories are empty immediately before removal to avoid race conditions
- **Chain Reaction Handling**: Automatically identifies parent directories that become empty after child removal
- **Dry Run Mode**: Preview what would be removed without making any changes
- **Symlink Handling**: Option to follow or ignore symbolic links
- **Detailed Logging**: Comprehensive output with timing statistics
- **Permission Error Handling**: Gracefully handles permission issues with clear error messages

## Installation

You can install EmptyBye using the provided installation script:

```bash
./install.sh
```

This will create a symlink in `~/.local/bin/` and make the utility available in your PATH.

## Usage

```
usage: emptybye.py [-h] [--dry-run] [--follow-symlinks] [--verbose] directory

Find and remove empty directories using depth-first search.

positional arguments:
  directory          The root directory to search for empty directories

options:
  -h, --help         show this help message and exit
  --dry-run          Show what would be removed without actually removing anything
  --follow-symlinks  Follow symbolic links when determining if directories are empty
  --verbose, -v      Enable verbose logging
```

## Examples

### Basic usage

```bash
emptybye ~/Downloads
```

### Preview what would be removed

```bash
emptybye --dry-run ~/Pictures
```

### Follow symbolic links

```bash
emptybye --follow-symlinks ~/Documents
```

### Enable verbose logging

```bash
emptybye --verbose ~/Projects
```

## Use Cases

- Cleaning up after bulk file operations that leave empty directory structures
- Tidying project directories after moving or deleting content
- Post-processing after file organization or archiving tasks
- Maintaining tidy filesystem structure in development environments

## Technical Details

- Written in Python 3
- No external dependencies
- Efficient recursive algorithm with parent directory chain reaction handling
- Includes safety checks to prevent accidental data loss

## License

This project is part of the dotfiles collection and follows the same licensing terms.