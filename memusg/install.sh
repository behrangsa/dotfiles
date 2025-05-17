#!/bin/bash

set -euo pipefail

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"

echo -e "${BLUE}Installing memusg system memory visualization tool...${NC}"

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

# Check for required Python packages
echo "Checking Python dependencies..."
MISSING_DEPS=()

check_package() {
    local package=$1
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_DEPS+=("$package")
        return 1
    fi
    return 0
}

check_package "psutil" || true
check_package "matplotlib" || true
check_package "squarify" || true
check_package "numpy" || true

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Warning: The following required packages are missing:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo -e "  - $dep"
    done
    
    # Offer to install dependencies
    echo
    read -p "Would you like to install these dependencies with pip? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installing dependencies...${NC}"
        python3 -m pip install --user "${MISSING_DEPS[@]}"
        echo -e "${GREEN}Dependencies installed successfully!${NC}"
    else
        echo -e "${YELLOW}Please install the dependencies manually:${NC}"
        echo "python3 -m pip install --user ${MISSING_DEPS[*]}"
    fi
fi

# Make sure the script is executable
chmod +x "${SCRIPT_DIR}/memusg.py"

# Create or update symlink in ~/.local/bin
if [ -L "${INSTALL_DIR}/memusg" ]; then
    echo "Removing existing symlink..."
    rm "${INSTALL_DIR}/memusg"
fi

ln -s "${SCRIPT_DIR}/memusg.py" "${INSTALL_DIR}/memusg"
echo -e "${GREEN}Symlink created: ${INSTALL_DIR}/memusg -> ${SCRIPT_DIR}/memusg.py${NC}"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo -e "${GREEN}Installation successful!${NC}"
    echo -e "${YELLOW}Warning: ${INSTALL_DIR} is not in your PATH${NC}"
    echo "Add the following line to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):"
    echo "export PATH=\"\$PATH:${INSTALL_DIR}\""
else
    echo -e "${GREEN}Installation successful! You can now use 'memusg' command.${NC}"
fi

echo
echo -e "${BLUE}Usage examples:${NC}"
echo -e "  memusg                                  # Basic memory usage visualization"
echo -e "  memusg --group-by username              # Group processes by username"
echo -e "  memusg --min-memory 100 --top 20        # Show top 20 processes using >100MB"
echo -e "  memusg --help                           # Show all options"