#!/bin/bash
# install.sh - Installs the LMDB dump utility

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
UTIL_NAME="bu-lmdb-dump"
SCRIPT_FILE="dump.py"

log_info "Installing LMDB dump utility (${UTIL_NAME})..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed. Please install Python 3."
    exit 1
fi
log_info "Python 3 found."

# Make main script executable
if [ -f "${SCRIPT_DIR}/${SCRIPT_FILE}" ]; then
    chmod +x "${SCRIPT_DIR}/${SCRIPT_FILE}"
    log_info "Made ${SCRIPT_DIR}/${SCRIPT_FILE} executable."
else
    log_error "Main script ${SCRIPT_DIR}/${SCRIPT_FILE} not found."
    exit 1
fi

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    log_info "Creating directory ${INSTALL_DIR}..."
    mkdir -p "$INSTALL_DIR"
fi

# Create symlink for the main script
SYMLINK_PATH="${INSTALL_DIR}/${UTIL_NAME}"
if [ -L "${SYMLINK_PATH}" ] || [ -e "${SYMLINK_PATH}" ]; then
    log_info "Removing existing ${UTIL_NAME} from ${INSTALL_DIR}..."
    rm "${SYMLINK_PATH}"
fi

ln -s "${SCRIPT_DIR}/${SCRIPT_FILE}" "${SYMLINK_PATH}"
log_success "Created symlink: ${SYMLINK_PATH} -> ${SCRIPT_DIR}/${SCRIPT_FILE}"

# Check if required Python package is installed
PYTHON_DEP_NAME="lmdb" # Name for both import and pip install

log_info "Checking Python dependency: ${PYTHON_DEP_NAME}..."
if ! python3 -c "import importlib.util; exit(0) if importlib.util.find_spec('$PYTHON_DEP_NAME') else exit(1)" &> /dev/null; then
    log_warn "Python dependency '${PYTHON_DEP_NAME}' is missing."
    log_info "Attempting to install it with pip3..."
    # Use python3 -m pip to ensure using the pip associated with python3
    if python3 -m pip install --user "${PYTHON_DEP_NAME}"; then
        log_success "Successfully installed Python dependency: ${PYTHON_DEP_NAME}"
    else
        log_error "Failed to install Python dependency '${PYTHON_DEP_NAME}'. Please install it manually:"
        log_error "python3 -m pip install --user ${PYTHON_DEP_NAME}"
        exit 1
    fi
else
    log_info "Python dependency '${PYTHON_DEP_NAME}' is already satisfied."
fi

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    log_success "Installation of ${UTIL_NAME} successful!"
    log_warn "However, ${INSTALL_DIR} is not in your PATH."
    log_info "To use the '${UTIL_NAME}' command directly, add the following line to your shell configuration file (e.g., ~/.bashrc, ~/.zshrc, ~/.profile, or ~/.config/fish/config.fish):"
    log_info "  export PATH=\"\$PATH:${INSTALL_DIR}\""
    log_info "Then, restart your shell or source the configuration file (e.g., 'source ~/.bashrc')."
else
    log_success "Installation successful! You can now use the '${UTIL_NAME}' command."
fi

# Basic usage information
log_info ""
log_info "Basic usage examples for ${UTIL_NAME}:"
log_info "  ${UTIL_NAME} --db /path/to/your/lmdb_database_dir"
log_info "  ${UTIL_NAME} --db ./my_lmdb_data --output ./lmdb_exports"
log_info ""
log_info "Run '${UTIL_NAME} --help' for more options."

exit 0
