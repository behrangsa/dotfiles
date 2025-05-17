#!/bin/bash

set -euo pipefail

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"

echo "Installing imgtag..."

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

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Warning: Ollama is required but not found in PATH${NC}"
    echo "Please install Ollama from: https://ollama.ai/"
fi

# Check if ExifTool is installed
if ! command -v exiftool &> /dev/null; then
    echo -e "${YELLOW}Warning: ExifTool is required for metadata writing but not found in PATH${NC}"
    echo "Please install ExifTool: https://exiftool.org/"
    echo "  - On Ubuntu/Debian: sudo apt install libimage-exiftool-perl"
    echo "  - On macOS: brew install exiftool"
fi

# Check for required Python packages
echo "Checking Python dependencies..."
python3 -c "import PIL" 2>/dev/null || {
    echo -e "${YELLOW}Warning: Pillow (PIL) package is required${NC}"
    echo "Please install it: pip3 install pillow"
}

# Make sure the script is executable
chmod +x "${SCRIPT_DIR}/imgtag.py"

# Create or update symlink in ~/.local/bin
if [ -L "${INSTALL_DIR}/imgtag" ]; then
    echo "Removing existing symlink..."
    rm "${INSTALL_DIR}/imgtag"
fi

ln -s "${SCRIPT_DIR}/imgtag.py" "${INSTALL_DIR}/imgtag"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo -e "${GREEN}Installation successful!${NC}"
    echo -e "${YELLOW}Warning: ${INSTALL_DIR} is not in your PATH${NC}"
    echo "Add the following line to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
    echo "export PATH=\"\$PATH:${INSTALL_DIR}\""
else
    echo -e "${GREEN}Installation successful! You can now use 'imgtag' command.${NC}"
fi