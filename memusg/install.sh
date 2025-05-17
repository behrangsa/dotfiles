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
AUTO_INSTALL=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-auto-install)
            AUTO_INSTALL=false
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --no-auto-install    Don't automatically install dependencies"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

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

# Check if pip is installed
if ! command -v python3 -m pip &> /dev/null; then
    echo -e "${RED}Error: pip for Python 3 is required but not installed${NC}" >&2
    exit 1
fi

# Define path to requirements file
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
MISSING_DEPS=()

# Check if requirements file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}Error: Requirements file not found at ${REQUIREMENTS_FILE}${NC}" >&2
    exit 1
fi

# Check for required Python packages
echo "Checking Python dependencies..."

check_package() {
    local package=$1
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_DEPS+=("$package")
        return 1
    fi
    return 0
}

# Extract package names from requirements.txt (ignoring version constraints)
while read -r line || [ -n "$line" ]; do
    # Skip empty lines and comments
    if [[ -z "$line" || "$line" =~ ^# ]]; then
        continue
    fi
    
    # Extract package name (everything before >= or == or similar)
    package=$(echo "$line" | sed -E 's/([a-zA-Z0-9_\-]+).*/\1/')
    check_package "$package" || true
done < "$REQUIREMENTS_FILE"

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo -e "${YELLOW}The following required packages are missing:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo -e "  - $dep"
    done
    
    if [ "$AUTO_INSTALL" = true ]; then
        echo -e "${BLUE}Installing dependencies automatically...${NC}"
        python3 -m pip install --user -r "$REQUIREMENTS_FILE"
        
        # Verify installation
        INSTALL_FAILED=false
        for dep in "${MISSING_DEPS[@]}"; do
            if ! python3 -c "import $dep" 2>/dev/null; then
                echo -e "${RED}Failed to install $dep${NC}" >&2
                INSTALL_FAILED=true
            fi
        done
        
        if [ "$INSTALL_FAILED" = true ]; then
            echo -e "${RED}Some dependencies could not be installed automatically.${NC}" >&2
            echo -e "${YELLOW}Please install them manually:${NC}"
            echo "python3 -m pip install --user ${MISSING_DEPS[*]}"
        else
            echo -e "${GREEN}All dependencies installed successfully!${NC}"
        fi
    else
        echo -e "${YELLOW}Please install the dependencies manually:${NC}"
        echo "python3 -m pip install --user -r $REQUIREMENTS_FILE"
        
        # Ask if user wants to continue without installing
        echo
        read -p "Continue with installation anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Installation aborted.${NC}"
            exit 1
        fi
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