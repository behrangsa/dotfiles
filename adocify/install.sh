#!/bin/bash

# install.sh - Installation script for adocify module
#
# This script installs the adocify TypeScript/Node.js CLI tool for converting
# Markdown to AsciiDoc using AI-powered analysis.

set -euo pipefail

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_NAME="adocify"
BIN_DIR="$HOME/.local/bin"
SYMLINK_NAME="adocify"

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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js
    if ! command_exists node; then
        log_error "Node.js is not installed. Please install Node.js 18.0.0 or higher."
        exit 1
    fi
    
    local node_version
    node_version=$(node --version | sed 's/v//')
    local major_version
    major_version=$(echo "$node_version" | cut -d. -f1)
    
    if [ "$major_version" -lt 18 ]; then
        log_error "Node.js version $node_version is too old. Please install Node.js 18.0.0 or higher."
        exit 1
    fi
    
    log_success "Node.js $node_version detected"
    
    # Check npm
    if ! command_exists npm; then
        log_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    log_success "npm $(npm --version) detected"
    
    # Check for DEEPSEEK_API_KEY
    if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
        log_warn "DEEPSEEK_API_KEY environment variable is not set"
        log_warn "Please set it before using adocify: export DEEPSEEK_API_KEY=your_api_key"
    else
        log_success "DEEPSEEK_API_KEY environment variable is set"
    fi
}

# Install dependencies and build
install_dependencies() {
    log_info "Installing dependencies..."
    
    cd "$SCRIPT_DIR"
    
    if [ -f "package-lock.json" ]; then
        npm ci
    else
        npm install
    fi
    
    log_success "Dependencies installed"
    
    log_info "Building project..."
    npm run build
    
    log_success "Project built successfully"
}

# Create symlink
create_symlink() {
    log_info "Creating executable symlink..."
    
    # Create bin directory if it doesn't exist
    mkdir -p "$BIN_DIR"
    
    local executable_path="$SCRIPT_DIR/dist/index.js"
    local symlink_path="$BIN_DIR/$SYMLINK_NAME"
    
    # Make the built file executable
    chmod +x "$executable_path"
    
    # Remove existing symlink if it exists
    if [ -L "$symlink_path" ]; then
        log_warn "Removing existing symlink: $symlink_path"
        rm "$symlink_path"
    elif [ -f "$symlink_path" ]; then
        log_error "File exists at $symlink_path but is not a symlink"
        log_error "Please remove it manually and run the installer again"
        exit 1
    fi
    
    # Create new symlink
    ln -s "$executable_path" "$symlink_path"
    log_success "Symlink created: $symlink_path -> $executable_path"
    
    # Check if bin directory is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        log_warn "$BIN_DIR is not in your PATH"
        log_warn "Add this line to your ~/.bashrc or ~/.zshrc:"
        log_warn "export PATH=\"\$HOME/.local/bin:\$PATH\""
    else
        log_success "$BIN_DIR is in your PATH"
    fi
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local symlink_path="$BIN_DIR/$SYMLINK_NAME"
    
    if [ ! -x "$symlink_path" ]; then
        log_error "Installation verification failed: $symlink_path is not executable"
        exit 1
    fi
    
    # Test the command
    if "$symlink_path" --version >/dev/null 2>&1; then
        log_success "Installation verified successfully"
        log_info "You can now use 'adocify' command from anywhere"
    else
        log_error "Installation verification failed: command does not execute properly"
        exit 1
    fi
}

# Show usage information
show_usage() {
    log_info "Usage examples:"
    echo "  adocify convert                    # Convert all README.md files"
    echo "  adocify convert --verbose          # Convert with detailed output"
    echo "  adocify convert --concurrency 3    # Use 3 concurrent processes"
    echo "  adocify check                      # Check environment and dependencies"
    echo ""
    log_info "For more options, run: adocify --help"
}

# Clean up on failure
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Installation failed with exit code $exit_code"
        log_info "Cleaning up..."
        
        # Remove symlink if it was created
        local symlink_path="$BIN_DIR/$SYMLINK_NAME"
        if [ -L "$symlink_path" ]; then
            rm "$symlink_path"
            log_info "Removed symlink: $symlink_path"
        fi
    fi
    exit $exit_code
}

# Main installation function
main() {
    log_info "Starting installation of $MODULE_NAME..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    check_prerequisites
    install_dependencies
    create_symlink
    verify_installation
    
    log_success "Installation completed successfully!"
    echo ""
    show_usage
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Install the adocify CLI tool for converting Markdown to AsciiDoc."
            echo ""
            echo "Options:"
            echo "  -h, --help     Show this help message and exit"
            echo ""
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
    shift
done

# Run main function
main