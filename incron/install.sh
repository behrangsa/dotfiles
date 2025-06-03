#!/bin/bash

# Install script for cleanmeta module

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

install_cleanmeta() {
    local user_home="${HOME}"
    local screenshots_dir="${user_home}/Pictures/Screenshots"
    local vivaldi_dir="${user_home}/Pictures/Vivaldi Captures"
    local script_path="${SCRIPT_DIR}/cleanmeta.sh"
    local screenshots_entry="${screenshots_dir} IN_CLOSE_WRITE ${script_path} \$@"
    local vivaldi_entry="${vivaldi_dir} IN_CLOSE_WRITE ${script_path} \$@"

    # Ensure cleanmeta script exists and is executable
    if [ ! -f "$script_path" ]; then
        log_error "cleanmeta script not found: $script_path"
        return 1
    fi

    chmod +x "$script_path" || {
        log_error "Failed to make script executable: $script_path"
        return 1
    }

    # Ensure Screenshots directory exists
    if [ ! -d "$screenshots_dir" ]; then
        log_info "Creating directory: $screenshots_dir"
        mkdir -p "$screenshots_dir" || {
            log_error "Failed to create directory: $screenshots_dir"
            return 1
        }
    fi

    # Ensure Vivaldi Captures directory exists
    if [ ! -d "$vivaldi_dir" ]; then
        log_info "Creating directory: $vivaldi_dir"
        mkdir -p "$vivaldi_dir" || {
            log_error "Failed to create directory: $vivaldi_dir"
            return 1
        }
    fi

    # Add cleanmeta.sh to $HOME/.local/bin
    local target_dir="${HOME}/.local/bin"
    local target_script="${target_dir}/cleanmeta"

    if [ ! -d "$target_dir" ]; then
        log_info "Creating directory: $target_dir"
        mkdir -p "$target_dir" || {
            log_error "Failed to create directory: $target_dir"
            return 1
        }
    fi

    # Handle existing target file or symlink
    if [ -L "$target_script" ]; then
        # Check if symlink points to the correct script
        if [ "$(readlink "$target_script")" != "$script_path" ]; then
            log_info "Updating incorrect symlink: $target_script"
            rm "$target_script" || {
                log_error "Failed to remove existing symlink: $target_script"
                return 1
            }
        else
            log_info "Symlink already exists and is correct: $target_script"
            return 0
        fi
    elif [ -e "$target_script" ]; then
        # Target exists but is not a symlink, back it up
        local backup_script="${target_script}.bak"
        log_info "Backing up existing file: $target_script -> $backup_script"
        mv "$target_script" "$backup_script" || {
            log_error "Failed to backup existing file: $target_script"
            return 1
        }
    fi

    # Create symlink to script
    log_info "Creating symlink to cleanmeta at $target_script"
    ln -s "$script_path" "$target_script" || {
        log_error "Failed to create symlink at: $target_script"
        return 1
    }

    log_success "cleanmeta symlink created successfully at $target_script"

    # Check if incron service is available
    if ! command -v incrontab &> /dev/null; then
        log_warn "incrontab command not found. Please install incron package."
        log_warn "On Ubuntu: sudo apt install incron"
        return 1
    fi

    # Remove existing cleanmeta entries from incrontab (to ensure clean state)
    log_info "Removing any existing cleanmeta entries from incrontab"
    local temp_incrontab="/tmp/incrontab.$$"
    if incrontab -l 2>/dev/null | grep -v -F "$script_path" > "$temp_incrontab"; then
        incrontab "$temp_incrontab" || {
            log_error "Failed to update incrontab"
            rm -f "$temp_incrontab"
            return 1
        }
    else
        # No existing entries, create empty incrontab
        echo -n "" | incrontab -
    fi
    rm -f "$temp_incrontab"

    # Add both entries to incrontab
    log_info "Adding cleanmeta entries to incrontab"
    ( incrontab -l 2>/dev/null; echo "$screenshots_entry"; echo "$vivaldi_entry" ) | incrontab - || {
        log_error "Failed to add cleanmeta entries to incrontab"
        return 1
    }
    
    log_success "cleanmeta entries added to incrontab"
    log_info "Screenshots entry: $screenshots_entry"
    log_info "Vivaldi entry: $vivaldi_entry"

    # Check dependencies for cleanmeta script
    if ! command -v exiftool &> /dev/null; then
        log_warn "exiftool not found. Please install: sudo apt install libimage-exiftool-perl"
    fi

    if ! command -v pngcrush &> /dev/null; then
        log_warn "pngcrush not found. Please install: sudo apt install pngcrush"
    fi

    return 0
}

# Main installation process
main() {
    log_info "Installing cleanmeta module"

    install_cleanmeta

    local result=$?
    if [ $result -eq 0 ]; then
        log_success "cleanmeta module installation completed successfully"
    else
        log_error "cleanmeta module installation failed"
    fi

    return $result
}

# Run the main function
main