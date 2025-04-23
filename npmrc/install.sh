#!/bin/bash
# install.sh - Symlink ~/.npmrc to ./npmrc/.npmrc
# This script creates a symbolic link from the user's home directory .npmrc
# to the npmrc/.npmrc file in this repository, sets permissions, and handles backups.

set -euo pipefail

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Constants
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SOURCE_NPMRC="$SCRIPT_DIR/.npmrc"
TARGET_NPMRC="$HOME/.npmrc"
BACKUP_DIR="$HOME/.dotfiles_backup/npmrc"

# Ensure the source file exists
if [ ! -f "$SOURCE_NPMRC" ]; then
    log_error "Source .npmrc does not exist at $SOURCE_NPMRC."
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
if [[ $? -ne 0 ]]; then
    log_error "Failed to create backup directory: ${BACKUP_DIR}"
    exit 1
fi

# If the destination exists and is a regular file (not a symlink), back it up
if [ -f "$TARGET_NPMRC" ] && [ ! -L "$TARGET_NPMRC" ]; then
    BACKUP_FILE="$BACKUP_DIR/.npmrc.backup.$(date +%Y%m%d%H%M%S)"
    log_info "Backing up existing $TARGET_NPMRC to $BACKUP_FILE"
    mv "$TARGET_NPMRC" "$BACKUP_FILE"
    if [[ $? -ne 0 ]]; then
        log_error "Failed to backup existing .npmrc file."
        exit 1
    fi
fi

# If the symlink exists but points elsewhere, remove it
if [ -L "$TARGET_NPMRC" ] && [ "$(readlink "$TARGET_NPMRC")" != "$SOURCE_NPMRC" ]; then
    log_info "Removing incorrect symlink at $TARGET_NPMRC"
    rm "$TARGET_NPMRC"
    if [[ $? -ne 0 ]]; then
        log_error "Failed to remove incorrect symlink."
        exit 1
    fi
fi

# Set secure permissions on the source file *before* linking
log_info "Setting permissions (600) on source file: $SOURCE_NPMRC"
chmod 600 "$SOURCE_NPMRC"
if [[ $? -ne 0 ]]; then
    log_warn "Failed to set permissions on source .npmrc file. Proceeding anyway."
    # Continue, but warn the user. Permissions are important for .npmrc.
fi

# Create the symlink if it doesn't exist
if [ ! -L "$TARGET_NPMRC" ]; then
    log_info "Creating symlink: $TARGET_NPMRC -> $SOURCE_NPMRC"
    ln -s "$SOURCE_NPMRC" "$TARGET_NPMRC"
    if [[ $? -ne 0 ]]; then
        log_error "Failed to create symbolic link."
        # Attempt to clean up potentially broken link
        rm -f "$TARGET_NPMRC"
        exit 1
    fi
    log_success "Symlink created successfully."
else
    log_info "Symlink already exists and is correct: $TARGET_NPMRC -> $SOURCE_NPMRC"
fi

log_success "npmrc module installation complete."
exit 0
