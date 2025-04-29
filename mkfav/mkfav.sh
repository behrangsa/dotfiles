#!/bin/bash

# mkfav.sh - A utility to create a favicon.ico from an image file
#
# This script takes an input image file and generates a favicon.ico file
# with multiple sizes (16x16, 32x32, 48x48, 256x256) using ImageMagick's
# convert command.

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

# Function to check if ImageMagick is installed
check_imagemagick() {
    if ! command -v convert &> /dev/null; then
        log_error "ImageMagick 'convert' command not found."
        log_error "Please install ImageMagick (e.g. 'sudo apt install imagemagick' or 'brew install imagemagick')"
        exit 1
    fi
    log_info "ImageMagick detected"
}

# Function to create favicon
create_favicon() {
    local input_file="$1"
    local output_file="${2:-favicon.ico}"
    
    # Check if input file exists
    if [ ! -f "$input_file" ]; then
        log_error "Input file does not exist: $input_file"
        exit 1
    fi
    
    # Check if input file is readable
    if [ ! -r "$input_file" ]; then
        log_error "Input file is not readable: $input_file"
        exit 1
    fi
    
    # Ensure output directory is writable
    local output_dir=$(dirname "$output_file")
    if [ ! -w "$output_dir" ] && [ "$output_dir" != "" ]; then
        log_error "Output directory is not writable: $output_dir"
        exit 1
    fi
    
    log_info "Creating favicon from $input_file"
    log_info "Output will be saved as $output_file"
    
    # Execute the convert command
    if convert "$input_file" \
        \( -clone 0 -resize 16x16! \) \
        \( -clone 0 -resize 32x32! \) \
        \( -clone 0 -resize 48x48! \) \
        \( -clone 0 -resize 256x256! \) \
        -delete 0 \
        "$output_file"; then
        
        log_success "Favicon created successfully: $output_file"
        return 0
    else
        local exit_code=$?
        log_error "Failed to create favicon (error code: $exit_code)"
        return 1
    fi
}

# Show usage information
show_usage() {
    echo "Usage: mkfav [OPTIONS] INPUT_FILE [OUTPUT_FILE]"
    echo ""
    echo "Create a favicon.ico file from an input image."
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message and exit"
    echo ""
    echo "Arguments:"
    echo "  INPUT_FILE     Path to the input image file"
    echo "  OUTPUT_FILE    Path to the output favicon file (default: favicon.ico in current directory)"
    echo ""
    echo "Examples:"
    echo "  mkfav logo.png"
    echo "  mkfav logo.png custom_favicon.ico"
    echo "  mkfav /path/to/image.jpg /path/to/output/favicon.ico"
}

# Main function
main() {
    # Process command line arguments
    local input_file=""
    local output_file="favicon.ico"
    
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [ -z "$input_file" ]; then
                    input_file="$1"
                elif [ -z "$output_file" ] || [ "$output_file" = "favicon.ico" ]; then
                    output_file="$1"
                else
                    log_error "Too many arguments"
                    show_usage
                    exit 1
                fi
                ;;
        esac
        shift
    done
    
    # Check if input file was provided
    if [ -z "$input_file" ]; then
        log_error "Input file not specified"
        show_usage
        exit 1
    fi
    
    # Check if ImageMagick is installed
    check_imagemagick
    
    # Create the favicon
    create_favicon "$input_file" "$output_file"
    
    exit $?
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi