#!/bin/bash

# Install script for mkfav module

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

install_mkfav() {
    local target_dir="${HOME}/.local/bin"
    local source_script="${SCRIPT_DIR}/mkfav.sh"
    local target_script="${target_dir}/mkfav"

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

    # Copy script to target directory
    log_info "Installing mkfav to $target_script"
    cp "$source_script" "$target_script" || {
        log_error "Failed to copy script to: $target_script"
        return 1
    }

    # Ensure target script is executable
    chmod +x "$target_script" || {
        log_error "Failed to make target script executable: $target_script"
        return 1
    }

    log_success "mkfav installed successfully to $target_script"

    # Verify ImageMagick installation
    if ! command -v convert &> /dev/null; then
        log_warn "ImageMagick 'convert' command not found. mkfav requires ImageMagick to function properly."
        log_warn "Please install ImageMagick (e.g. 'sudo apt install imagemagick' or 'brew install imagemagick')"
    fi

    return 0
}

# Main installation process
main() {
    log_info "Installing mkfav module"

    install_mkfav

    local result=$?
    if [ $result -eq 0 ]; then
        log_success "mkfav module installation completed successfully"
    else
        log_error "mkfav module installation failed"
    fi

    return $result
}

# Run the main function
main
