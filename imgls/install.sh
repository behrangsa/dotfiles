#!/bin/bash

# Install script for imgls module

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

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

install_imgls() {
    local target_dir="${HOME}/.local/bin"
    local source_script="${SCRIPT_DIR}/imgls.sh"
    local target_script="${target_dir}/imgls"

    # Ensure source script exists and is executable
    if [ ! -f "$source_script" ]; then
        log_error "Source script not found: $source_script"
        return 1
    fi

    # Make sure the script is executable
    chmod +x "$source_script" || {
        log_error "Failed to make script executable: $source_script"
        return 1
    }

    # Create target directory if it doesn't exist
    if [ ! -d "$target_dir" ]; then
        log_info "Creating directory: $target_dir"
        mkdir -p "$target_dir" || {
            log_error "Failed to create directory: $target_dir"
            return 1
        }
    fi

    # Remove existing symlink if it exists
    if [ -L "$target_script" ]; then
        log_info "Removing existing symlink: $target_script"
        rm "$target_script" || {
            log_error "Failed to remove existing symlink: $target_script"
            return 1
        }
    elif [ -e "$target_script" ]; then
        log_error "Target exists and is not a symlink: $target_script"
        return 1
    fi

    # Create symlink to script
    log_info "Creating symlink to imgls at $target_script"
    ln -s "$source_script" "$target_script" || {
        log_error "Failed to create symlink at: $target_script"
        return 1
    }

    log_success "imgls symlink created successfully at $target_script"

    # Verify dependencies
    if ! command -v kitty &> /dev/null; then
        log_warn "Kitty terminal emulator not found. imgls requires Kitty to function properly."
        log_warn "Please install Kitty (e.g. 'sudo apt install kitty' or visit https://sw.kovidgoyal.net/kitty/)"
    fi

    if ! command -v tput &> /dev/null; then
        log_warn "tput command not found. imgls requires ncurses to function properly."
        log_warn "Please install ncurses (e.g. 'sudo apt install ncurses-bin')"
    fi

    return 0
}

# Main installation process
main() {
    log_info "Installing imgls module"

    install_imgls

    local result=$?
    if [ $result -eq 0 ]; then
        log_success "imgls module installation completed successfully"
    else
        log_error "imgls module installation failed"
    fi

    return $result
}

# Run the main function
main