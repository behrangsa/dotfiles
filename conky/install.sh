#!/bin/bash
# install.sh - Symlink conky configuration files from repository to home directory
# This script creates symbolic links from the user's home directory to any conky
# configuration files in this repository matching the pattern \.conky.*rc,
# with error handling and safety checks.

set -euo pipefail

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME"

echo "Setting up Conky configuration files..."

# Find all files in the repo's conky directory that match the pattern
while IFS= read -r source_file; do
    if [ -z "$source_file" ]; then
        continue
    fi

    # Get just the filename for the target link
    filename=$(basename "$source_file")
    target_link="$TARGET_DIR/$filename"

    # Check if the source file exists (should always be true but checking for safety)
    if [ ! -f "$source_file" ]; then
        echo "Error: Source file $source_file does not exist." >&2
        continue
    fi

    # If the destination exists and is not a symlink, back it up
    if [ -e "$target_link" ] && [ ! -L "$target_link" ]; then
        BACKUP="$target_link.backup.$(date +%Y%m%d%H%M%S)"
        echo "Backing up existing $target_link to $BACKUP"
        mv "$target_link" "$BACKUP"
    fi

    # If the symlink exists but points elsewhere, remove it
    if [ -L "$target_link" ] && [ "$(readlink "$target_link")" != "$source_file" ]; then
        echo "Removing incorrect symlink at $target_link"
        rm "$target_link"
    fi

    # Create the symlink if it doesn't exist or was removed
    if [ ! -L "$target_link" ]; then
        ln -s "$source_file" "$target_link"
        echo "Symlink created: $target_link -> $source_file"
    else
        echo "Symlink already exists and is correct: $target_link -> $source_file"
    fi
done < <(find "$SCRIPT_DIR" -maxdepth 1 -type f -name "\.conky*rc")

# Make sure our utility scripts are executable and symlinked to ~/.local/bin
bin_dir="$HOME/.local/bin"
if [ ! -d "$bin_dir" ]; then
    mkdir -p "$bin_dir"
    echo "Created $bin_dir directory"
fi

# Function to process a script (make executable and create symlink)
process_script() {
    local script_name="$1"
    local script_path="$SCRIPT_DIR/$script_name"

    if [ -f "$script_path" ]; then
        # Make executable
        chmod +x "$script_path"
        echo "Made $script_name executable"

        # Set up symlink
        local target_link="$bin_dir/$script_name"

        # If the symlink exists but points elsewhere, remove it
        if [ -L "$target_link" ] && [ "$(readlink "$target_link")" != "$script_path" ]; then
            echo "Removing incorrect symlink at $target_link"
            rm "$target_link"
        fi

        # Create the symlink if it doesn't exist or was removed
        if [ ! -L "$target_link" ]; then
            ln -s "$script_path" "$target_link"
            echo "Symlink created: $target_link -> $script_path"
        else
            echo "Symlink already exists and is correct: $target_link -> $script_path"
        fi
    else
        echo "Warning: Script $script_name not found in $SCRIPT_DIR"
    fi
}

# Process each utility script
process_script "vimtips.sh"
process_script "sensors.sh"
process_script "vnstati.sh"

echo "Conky configuration setup complete!"
