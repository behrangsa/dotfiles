#!/bin/bash

# Master installer for dotfiles
# This script automatically detects and calls each module's installer sequentially

set -euo pipefail

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

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

# Function to run a module installer
run_installer() {
    local module=$1
    local installer="$module"
    local module_name=$(basename "$(dirname "$installer")")
    
    log_info "Installing module: ${module_name}"
    if bash "$installer"; then
        log_success "Module ${module_name} installed successfully"
        return 0
    else
        log_error "Failed to install module: ${module_name}"
        return 1
    fi
}

# Main installation process
main() {
    log_info "Starting dotfiles installation on $(date)"
    
    # Find all install.sh scripts in subdirectories
    mapfile -t installers < <(find "$SCRIPT_DIR" -mindepth 2 -maxdepth 2 -name "install.sh" -type f | sort)
    
    if [ ${#installers[@]} -eq 0 ]; then
        log_warn "No module installers found."
        exit 0
    fi
    
    log_info "Found ${#installers[@]} modules to install: $(for i in "${installers[@]}"; do basename "$(dirname "$i")"; done | tr '\n' ' ')"
    
    # Track failures
    failures=()
    
    # Install each module sequentially
    for installer in "${installers[@]}"; do
        if ! run_installer "$installer"; then
            failures+=("$(basename "$(dirname "$installer")")")
        fi
    done
    
    # Summary
    echo ""
    log_info "Installation completed on $(date)"
    
    if [ ${#failures[@]} -eq 0 ]; then
        log_success "All modules installed successfully"
    else
        log_warn "Some modules failed to install: ${failures[*]}"
        exit 1
    fi
}

# Run the main function
main "$@"
