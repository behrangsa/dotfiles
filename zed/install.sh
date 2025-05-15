#!/bin/bash
# install.sh - Symlink ~/.config/zed/settings.json to ./zed/settings.json
# This script creates a symbolic link from the user's ~/.config/zed/settings.json
# to the zed/settings.json file in this repository, with error handling and safety checks.

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_SETTINGS="$SCRIPT_DIR/settings.json"
ZED_CONFIG_DIR="$HOME/.config/zed"
TARGET_SETTINGS="$ZED_CONFIG_DIR/settings.json"

# Check if the source file exists
if [ ! -f "$REPO_SETTINGS" ]; then
    echo "Error: Source settings.json does not exist at $REPO_SETTINGS." >&2
    exit 1
fi

# Create Zed config directory if it doesn't exist
if [ ! -d "$ZED_CONFIG_DIR" ]; then
    echo "Creating Zed configuration directory at $ZED_CONFIG_DIR"
    mkdir -p "$ZED_CONFIG_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create Zed configuration directory." >&2
        exit 1
    fi
fi

# If the destination exists and is not a symlink to the right place, back it up
if [ -e "$TARGET_SETTINGS" ] && [ ! -L "$TARGET_SETTINGS" ]; then
    BACKUP="$TARGET_SETTINGS.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing $TARGET_SETTINGS to $BACKUP"
    mv "$TARGET_SETTINGS" "$BACKUP"
fi

# If the symlink exists but points elsewhere, remove it
if [ -L "$TARGET_SETTINGS" ] && [ "$(readlink "$TARGET_SETTINGS")" != "$REPO_SETTINGS" ]; then
    echo "Removing incorrect symlink at $TARGET_SETTINGS"
    rm "$TARGET_SETTINGS"
fi

# Create the symlink if it doesn't exist
if [ ! -L "$TARGET_SETTINGS" ]; then
    ln -s "$REPO_SETTINGS" "$TARGET_SETTINGS"
    echo "Symlink created: $TARGET_SETTINGS -> $REPO_SETTINGS"
else
    echo "Symlink already exists and is correct: $TARGET_SETTINGS -> $REPO_SETTINGS"
fi

echo "Zed module installation complete."