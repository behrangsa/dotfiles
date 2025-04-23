#!/bin/bash

set -euo pipefail

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"

echo "Installing emptybye..."

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating directory ${INSTALL_DIR}..."
    mkdir -p "$INSTALL_DIR"
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}" >&2
    exit 1
fi

# Make sure the Python script is executable
chmod +x "${SCRIPT_DIR}/emptybye.py"

# Create symlink in ~/.local/bin
if [ -L "${INSTALL_DIR}/emptybye" ]; then
    echo "Removing existing symlink..."
    rm "${INSTALL_DIR}/emptybye"
fi

ln -s "${SCRIPT_DIR}/emptybye.py" "${INSTALL_DIR}/emptybye"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo -e "${GREEN}Installation successful!${NC}"
    echo -e "${RED}Warning: ${INSTALL_DIR} is not in your PATH${NC}"
    echo "Add the following line to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
    echo "export PATH=\"\$PATH:${INSTALL_DIR}\""
else
    echo -e "${GREEN}Installation successful! You can now use 'emptybye' command.${NC}"
fi