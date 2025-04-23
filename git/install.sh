#!/bin/bash
# install.sh - Symlink ~/.gitconfig to ./git/.gitconfig
# This script creates a symbolic link from the user's home directory .gitconfig
# to the git/.gitconfig file in this repository, with error handling and safety checks.

set -euo pipefail

# Constants
REPO_GITCONFIG="$(cd "$(dirname "$0")" && pwd)/.gitconfig"
HOME_GITCONFIG="$HOME/.gitconfig"

# Check if the source file exists
if [ ! -f "$REPO_GITCONFIG" ]; then
    echo "Error: Source git/.gitconfig does not exist at $REPO_GITCONFIG." >&2
    exit 1
fi

# If the destination exists and is not a symlink to the right place, back it up
if [ -e "$HOME_GITCONFIG" ] && [ ! -L "$HOME_GITCONFIG" ]; then
    BACKUP="$HOME_GITCONFIG.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing $HOME_GITCONFIG to $BACKUP"
    mv "$HOME_GITCONFIG" "$BACKUP"
fi

# If the symlink exists but points elsewhere, remove it
if [ -L "$HOME_GITCONFIG" ] && [ "$(readlink "$HOME_GITCONFIG")" != "$REPO_GITCONFIG" ]; then
    echo "Removing incorrect symlink at $HOME_GITCONFIG"
    rm "$HOME_GITCONFIG"
fi

# Create the symlink if it doesn't exist
if [ ! -L "$HOME_GITCONFIG" ]; then
    ln -s "$REPO_GITCONFIG" "$HOME_GITCONFIG"
    echo "Symlink created: $HOME_GITCONFIG -> $REPO_GITCONFIG"
else
    echo "Symlink already exists and is correct: $HOME_GITCONFIG -> $REPO_GITCONFIG"
fi

