#!/bin/bash
# install.sh - Installs the pngcrush utility wrapper

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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"

log_info "Installing pngcrush utility wrapper..."

# Check if pngcrush is installed
if ! command -v pngcrush &> /dev/null; then
    log_error "pngcrush is required but not installed. Please install it first."
    exit 1
fi

# Make script executable
chmod +x "${SCRIPT_DIR}/crush.sh"

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    log_info "Creating directory ${INSTALL_DIR}..."
    mkdir -p "$INSTALL_DIR"
fi

# Create symlink for the main script
if [ -L "${INSTALL_DIR}/crush-pngs" ] || [ -e "${INSTALL_DIR}/crush-pngs" ]; then
    log_info "Removing existing crush-pngs..."
    rm "${INSTALL_DIR}/crush-pngs"
fi

ln -s "${SCRIPT_DIR}/crush.sh" "${INSTALL_DIR}/crush-pngs"
log_success "Created symlink: ${INSTALL_DIR}/crush-pngs -> ${SCRIPT_DIR}/crush.sh"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    log_success "Installation successful!"
    log_warn "Warning: ${INSTALL_DIR} is not in your PATH"
    log_info "Add the following line to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
    log_info "export PATH=\"$PATH:${INSTALL_DIR}\""
else
    log_success "Installation successful! You can now use 'crush-pngs' command."
fi

# Basic usage information
log_info "Basic usage example:"
log_info "  crush-pngs"
