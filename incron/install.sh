#!/bin/bash

# install.sh - Installation script for the Automated Image Metadata Cleaner
# Sets up incron monitoring, dependencies, and directory structure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLEANMETA_SCRIPT="$SCRIPT_DIR/cleanmeta.sh"
LOCAL_BIN="$HOME/.local/bin"
CLEANMETA_SYMLINK="$LOCAL_BIN/cleanmeta"
SCREENSHOTS_DIR="$HOME/Pictures/Screenshots"
# Incron-compatible directories (without spaces)
SCREENSHOTS_INCRON_DIR="$HOME/Pictures/Screenshots"
VIVALDI_INCRON_DIR="$HOME/Pictures/.vivaldicaptures"

# Try to detect the actual Vivaldi directory name
if [[ -d "$HOME/Pictures/Vivaldi Screenshots" ]]; then
    VIVALDI_ACTUAL_DIR="$HOME/Pictures/Vivaldi Screenshots"
    VIVALDI_DIR_FOUND="Vivaldi Screenshots"
elif [[ -d "$HOME/Pictures/Vivaldi Captures" ]]; then
    VIVALDI_ACTUAL_DIR="$HOME/Pictures/Vivaldi Captures"
    VIVALDI_DIR_FOUND="Vivaldi Captures"
else
    # Default to Vivaldi Screenshots (more common)
    VIVALDI_ACTUAL_DIR="$HOME/Pictures/Vivaldi Screenshots"
    VIVALDI_DIR_FOUND="Vivaldi Screenshots (default)"
fi

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        log_error "Run as regular user - sudo will be used when needed"
        exit 1
    fi
}

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check for systemd (required for incron service)
    if ! command -v systemctl >/dev/null 2>&1; then
        log_error "systemctl not found - systemd is required"
        exit 1
    fi
    
    # Check for package manager
    if ! command -v apt >/dev/null 2>&1; then
        log_error "apt package manager not found - Ubuntu/Debian required"
        exit 1
    fi
    
    log_success "System requirements met"
}

# Install required packages
install_dependencies() {
    log_info "Installing required packages..."
    
    local packages=("incron" "libimage-exiftool-perl" "pngcrush")
    local missing_packages=()
    
    # Check which packages are missing
    for package in "${packages[@]}"; do
        if ! dpkg -l "$package" >/dev/null 2>&1; then
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -eq 0 ]]; then
        log_success "All required packages are already installed"
        return 0
    fi
    
    log_info "Installing missing packages: ${missing_packages[*]}"
    
    # Update package list
    if ! sudo apt update; then
        log_error "Failed to update package list"
        exit 1
    fi
    
    # Install missing packages
    if ! sudo apt install -y "${missing_packages[@]}"; then
        log_error "Failed to install required packages"
        exit 1
    fi
    
    log_success "Dependencies installed successfully"
}

# Create directory structure
create_directories() {
    log_info "Creating directory structure..."
    
    # Create local bin directory
    if [[ ! -d "$LOCAL_BIN" ]]; then
        mkdir -p "$LOCAL_BIN"
        log_info "Created $LOCAL_BIN"
    fi
    
    # Create Screenshots directory if it doesn't exist
    if [[ ! -d "$SCREENSHOTS_DIR" ]]; then
        mkdir -p "$SCREENSHOTS_DIR"
        log_info "Created $SCREENSHOTS_DIR"
    fi
    
    # Create actual Vivaldi directory if it doesn't exist
    if [[ ! -d "$VIVALDI_ACTUAL_DIR" ]]; then
        mkdir -p "$VIVALDI_ACTUAL_DIR"
        log_info "Created $VIVALDI_ACTUAL_DIR"
    fi
    
    log_info "Detected Vivaldi directory: $VIVALDI_DIR_FOUND"
    
    # Create symbolic link for Vivaldi directory if it has spaces
    if [[ "$VIVALDI_ACTUAL_DIR" != "$VIVALDI_INCRON_DIR" ]]; then
        # Remove existing symlink if it exists
        if [[ -L "$VIVALDI_INCRON_DIR" ]]; then
            rm "$VIVALDI_INCRON_DIR"
            log_info "Removed existing Vivaldi symlink"
        fi
        
        # Create new symlink
        if ln -s "$VIVALDI_ACTUAL_DIR" "$VIVALDI_INCRON_DIR"; then
            log_info "Created symlink: $VIVALDI_INCRON_DIR -> $VIVALDI_ACTUAL_DIR"
        else
            log_error "Failed to create Vivaldi symlink"
            exit 1
        fi
    fi
    
    # Create lock directory
    mkdir -p "/tmp/cleanmeta.locks"
    
    log_success "Directory structure created"
}

# Create symlink to cleanmeta script
create_symlink() {
    log_info "Creating symlink to cleanmeta script..."
    
    # Check if cleanmeta.sh exists and is executable
    if [[ ! -f "$CLEANMETA_SCRIPT" ]]; then
        log_error "cleanmeta.sh not found at $CLEANMETA_SCRIPT"
        exit 1
    fi
    
    if [[ ! -x "$CLEANMETA_SCRIPT" ]]; then
        chmod +x "$CLEANMETA_SCRIPT"
        log_info "Made cleanmeta.sh executable"
    fi
    
    # Remove existing symlink if it exists
    if [[ -L "$CLEANMETA_SYMLINK" ]]; then
        rm "$CLEANMETA_SYMLINK"
        log_info "Removed existing symlink"
    fi
    
    # Create new symlink
    if ln -s "$CLEANMETA_SCRIPT" "$CLEANMETA_SYMLINK"; then
        log_success "Created symlink: $CLEANMETA_SYMLINK -> $CLEANMETA_SCRIPT"
    else
        log_error "Failed to create symlink"
        exit 1
    fi
    
    # Ensure ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        log_warning "~/.local/bin is not in your PATH"
        log_warning "Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
        echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# Configure incron service
configure_incron_service() {
    log_info "Configuring incron service..."
    
    # Enable and start incron service
    if ! sudo systemctl is-enabled incron >/dev/null 2>&1; then
        sudo systemctl enable incron
        log_info "Enabled incron service"
    fi
    
    if ! sudo systemctl is-active incron >/dev/null 2>&1; then
        sudo systemctl start incron
        log_info "Started incron service"
    fi
    
    # Add user to incron.allow if file exists
    if [[ -f "/etc/incron.allow" ]]; then
        if ! grep -q "^$USER$" /etc/incron.allow 2>/dev/null; then
            echo "$USER" | sudo tee -a /etc/incron.allow >/dev/null
            log_info "Added $USER to /etc/incron.allow"
        fi
    fi
    
    # Remove user from incron.deny if file exists
    if [[ -f "/etc/incron.deny" ]]; then
        if grep -q "^$USER$" /etc/incron.deny 2>/dev/null; then
            sudo sed -i "/^$USER$/d" /etc/incron.deny
            log_info "Removed $USER from /etc/incron.deny"
        fi
    fi
    
    log_success "Incron service configured"
}

# Setup incron monitoring entries
setup_incron_entries() {
    log_info "Setting up incron monitoring entries..."
    
    # Remove existing entries for these directories
    if incrontab -l 2>/dev/null | grep -q "$CLEANMETA_SCRIPT"; then
        log_info "Removing existing incron entries..."
        incrontab -l 2>/dev/null | grep -v "$CLEANMETA_SCRIPT" | incrontab - 2>/dev/null || true
    fi
    
    # Create temporary incrontab file
    local temp_incrontab=$(mktemp)
    
    # Get existing entries (if any)
    incrontab -l 2>/dev/null > "$temp_incrontab" || true
    
    # Add new entries (using space-free paths for incron compatibility)
    # Listen to multiple events to catch different screenshot creation methods
    log_info "Adding incron entry for: $SCREENSHOTS_INCRON_DIR"
    printf '%s IN_CLOSE_WRITE,IN_MODIFY,IN_MOVED_TO,loopable=true %s $@/$#\n' "$SCREENSHOTS_INCRON_DIR" "$CLEANMETA_SCRIPT" >> "$temp_incrontab"
    
    log_info "Adding incron entry for: $VIVALDI_INCRON_DIR"
    printf '%s IN_CLOSE_WRITE,IN_MODIFY,IN_MOVED_TO,loopable=true %s $@/$#\n' "$VIVALDI_INCRON_DIR" "$CLEANMETA_SCRIPT" >> "$temp_incrontab"
    
    log_info "Contents of temp incrontab file:"
    cat "$temp_incrontab" | while read line; do
        log_info "  $line"
    done
    
    # Install the incrontab
    if incrontab "$temp_incrontab"; then
        log_success "Incron entries installed successfully"
    else
        log_error "Failed to install incron entries"
        rm -f "$temp_incrontab"
        exit 1
    fi
    
    # Clean up
    rm -f "$temp_incrontab"
    
    # Restart incron to reload configuration
    sudo systemctl restart incron
    log_info "Restarted incron service"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local errors=0
    
    # Check symlink
    if [[ ! -L "$CLEANMETA_SYMLINK" ]] || [[ ! -x "$CLEANMETA_SYMLINK" ]]; then
        log_error "Symlink verification failed"
        ((errors++))
    fi
    
    # Check incron service
    if ! sudo systemctl is-active incron >/dev/null 2>&1; then
        log_error "Incron service is not running"
        ((errors++))
    fi
    
    # Check dependencies
    for cmd in exiftool pngcrush; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            log_error "Missing dependency: $cmd"
            ((errors++))
        fi
    done
    
    # Check incron entries
    if ! incrontab -l 2>/dev/null | grep -q "$CLEANMETA_SCRIPT"; then
        log_error "Incron entries not found"
        ((errors++))
    fi
    
    # Test cleanmeta script
    if ! "$CLEANMETA_SYMLINK" --help >/dev/null 2>&1; then
        log_error "cleanmeta script test failed"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log_success "Installation verification passed"
        return 0
    else
        log_error "Installation verification failed with $errors errors"
        return 1
    fi
}

# Show installation summary
show_summary() {
    echo ""
    echo "=========================================="
    echo "  Installation Summary"
    echo "=========================================="
    echo ""
    echo "✓ Dependencies installed (incron, exiftool, pngcrush)"
    echo "✓ Directory structure created:"
    echo "  - $SCREENSHOTS_DIR"
    echo "  - $VIVALDI_ACTUAL_DIR"
    if [[ "$VIVALDI_ACTUAL_DIR" != "$VIVALDI_INCRON_DIR" ]]; then
        echo "  - $VIVALDI_INCRON_DIR (symlink for incron compatibility)"
    fi
    echo "✓ Symlink created: $CLEANMETA_SYMLINK"
    echo "✓ Incron service configured and running"
    echo "✓ Monitoring entries installed:"
    echo "  - Screenshots directory"
    echo "  - $VIVALDI_DIR_FOUND directory"
    echo ""
    echo "The system is now monitoring for new image files and will"
    echo "automatically process them to remove metadata and organize"
    echo "them into date-based directory structures."
    echo ""
    echo "Debug log: /tmp/cleanmeta.debug.log"
    echo "Manual usage: cleanmeta [--debug] <file>"
    echo ""
    echo "To verify monitoring is working:"
    echo "  tail -f /tmp/cleanmeta.debug.log"
    echo "  journalctl -u incron -f"
    echo ""
}

# Main installation function
main() {
    echo "=========================================="
    echo "  Automated Image Metadata Cleaner"
    echo "  Installation Script"
    echo "=========================================="
    echo ""
    
    check_not_root
    check_system_requirements
    install_dependencies
    create_directories
    create_symlink
    configure_incron_service
    setup_incron_entries
    
    if verify_installation; then
        show_summary
        log_success "Installation completed successfully!"
        exit 0
    else
        log_error "Installation completed with errors"
        echo ""
        echo "Please check the error messages above and try again."
        echo "You can also check the incron service status:"
        echo "  sudo systemctl status incron"
        echo "  incrontab -l"
        exit 1
    fi
}

# Handle script interruption
cleanup() {
    log_warning "Installation interrupted"
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"