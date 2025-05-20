#!/bin/bash
# install.sh - Installs the SQLite dump utility

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

log_info "Installing SQLite dump utility..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

# Make scripts executable
chmod +x "${SCRIPT_DIR}/dump.py"

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    log_info "Creating directory ${INSTALL_DIR}..."
    mkdir -p "$INSTALL_DIR"
fi

# Create symlink for the main script
if [ -L "${INSTALL_DIR}/bu-sqlite-dump" ] || [ -e "${INSTALL_DIR}/bu-sqlite-dump" ]; then
    log_info "Removing existing bu-sqlite-dump..."
    rm "${INSTALL_DIR}/bu-sqlite-dump"
fi

ln -s "${SCRIPT_DIR}/dump.py" "${INSTALL_DIR}/bu-sqlite-dump"
log_success "Created symlink: ${INSTALL_DIR}/bu-sqlite-dump -> ${SCRIPT_DIR}/dump.py"

# Check if required Python packages are installed
PYTHON_DEPS=("pandas") # sqlite3 is part of the standard library
MISSING_DEPS=()

for dep in "${PYTHON_DEPS[@]}"; do
    if ! python3 -c "import $dep" &> /dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log_warn "The following Python dependencies are missing: ${MISSING_DEPS[*]}"
    log_info "Installing them with pip..."
    pip3 install --user "${MISSING_DEPS[@]}" || {
        log_error "Failed to install Python dependencies. Please install them manually:"
        log_error "pip3 install --user ${MISSING_DEPS[*]}"
        exit 1
    }
fi

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    log_success "Installation successful!"
    log_warn "Warning: ${INSTALL_DIR} is not in your PATH"
    log_info "Add the following line to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
    log_info "export PATH=\"\$PATH:${INSTALL_DIR}\""
else
    log_success "Installation successful! You can now use 'bu-sqlite-dump' command."
fi

# Basic usage information
log_info "Basic usage examples:"
log_info "  bu-sqlite-dump --db mydatabase.db                 # Export tables to current directory"
log_info "  bu-sqlite-dump --db mydatabase.db --output ./export  # Export to specific directory"