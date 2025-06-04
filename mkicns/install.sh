#!/bin/bash
# install.sh - Installs the mkicns utility

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

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"

log_info "Installing mkicns utility..."

# Check if bash is available
if ! command -v bash &> /dev/null; then
    log_error "Bash is required but not installed"
    exit 1
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    log_warn "ImageMagick 'convert' not found. Please install it for mkicns to work."
fi

# Check if png2icns is installed
if ! command -v png2icns &> /dev/null; then
    log_warn "'png2icns' not found. Please install it for mkicns to work."
fi

# Make script executable
chmod +x "${SCRIPT_DIR}/mkicns.sh"

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    log_info "Creating directory ${INSTALL_DIR}..."
    mkdir -p "$INSTALL_DIR"
fi

# Create symlink for the main script
if [ -L "${INSTALL_DIR}/mkicns" ] || [ -e "${INSTALL_DIR}/mkicns" ]; then
    log_info "Removing existing mkicns..."
    rm "${INSTALL_DIR}/mkicns"
fi

ln -s "${SCRIPT_DIR}/mkicns.sh" "${INSTALL_DIR}/mkicns"
log_success "Created symlink: ${INSTALL_DIR}/mkicns -> ${SCRIPT_DIR}/mkicns.sh"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    log_success "Installation successful!"
    log_warn "Warning: ${INSTALL_DIR} is not in your PATH"
    log_info "Add the following line to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
    log_info "export PATH=\"\$PATH:${INSTALL_DIR}\""
else
    log_success "Installation successful! You can now use 'mkicns' command."
fi

# Basic usage information
log_info "Basic usage examples:"
log_info "  mkicns -d ./icons"
log_info "  mkicns --directory /path/to/pngs"