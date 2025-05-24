#!/bin/bash
# install.sh - Symlink ~/.config/topydo/config and columns to ./topydo/config and ./topydo/columns
# This script creates symbolic links from the user's ~/.config/topydo/ directory
# to the config and columns files in this repository, with error handling and safety checks.

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CONFIG="$SCRIPT_DIR/config"
REPO_COLUMNS="$SCRIPT_DIR/columns"
TOPYDO_CONFIG_DIR="$HOME/.config/topydo"
TARGET_CONFIG="$TOPYDO_CONFIG_DIR/config"
TARGET_COLUMNS="$TOPYDO_CONFIG_DIR/columns"

# Check if the source files exist
if [ ! -f "$REPO_CONFIG" ]; then
    echo "Error: Source config does not exist at $REPO_CONFIG." >&2
    exit 1
fi
if [ ! -f "$REPO_COLUMNS" ]; then
    echo "Error: Source columns does not exist at $REPO_COLUMNS." >&2
    exit 1
fi

# Create Topydo config directory if it doesn't exist
if [ ! -d "$TOPYDO_CONFIG_DIR" ]; then
    echo "Creating Topydo configuration directory at $TOPYDO_CONFIG_DIR"
    mkdir -p "$TOPYDO_CONFIG_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create Topydo configuration directory." >&2
        exit 1
    fi
fi

# Function to handle symlinking with backup and correction
symlink_with_backup() {
    local src="$1"
    local dest="$2"
    local name="$3"
    if [ -e "$dest" ] && [ ! -L "$dest" ]; then
        BACKUP="$dest.backup.$(date +%Y%m%d%H%M%S)"
        echo "Backing up existing $dest to $BACKUP"
        mv "$dest" "$BACKUP"
    fi
    if [ -L "$dest" ] && [ "$(readlink "$dest")" != "$src" ]; then
        echo "Removing incorrect symlink at $dest"
        rm "$dest"
    fi
    if [ ! -L "$dest" ]; then
        ln -s "$src" "$dest"
        echo "Symlink created: $dest -> $src"
    else
        echo "Symlink already exists and is correct: $dest -> $src"
    fi
}

# Symlink config and columns
symlink_with_backup "$REPO_CONFIG" "$TARGET_CONFIG" "config"
symlink_with_backup "$REPO_COLUMNS" "$TARGET_COLUMNS" "columns"

echo "Topydo module installation complete."
