#!/bin/bash

# mkicns.sh - Batch convert 1024x1024 PNGs to .icns files for macOS
#
# For each 1024x1024 PNG in the given directory, creates a subdirectory,
# generates 512x512, 256x256, and 128x128 variants, and builds an .icns file.
#
# Usage:
#   mkicns.sh -d /path/to/pngs
#   mkicns.sh --directory /path/to/pngs

set -euo pipefail

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check dependencies
check_dependencies() {
    if ! command -v convert &>/dev/null; then
        log_error "ImageMagick 'convert' not found. Please install it."
        exit 1
    fi
    if ! command -v png2icns &>/dev/null; then
        log_error "'png2icns' not found. Please install it."
        exit 1
    fi
    log_info "All dependencies detected"
}

# Show usage
show_usage() {
    echo "Usage: mkicns.sh -d DIRECTORY"
    echo ""
    echo "Batch convert 1024x1024 PNGs in DIRECTORY to .icns files."
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR   Directory containing 1024x1024 PNG files"
    echo "  -h, --help            Show this help message"
}

# Main logic
main() {
    local directory=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d|--directory)
                directory="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown argument: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    if [[ -z "$directory" ]]; then
        log_error "Directory not specified."
        show_usage
        exit 1
    fi

    if [[ ! -d "$directory" ]]; then
        log_error "Directory does not exist: $directory"
        exit 1
    fi

    check_dependencies

    shopt -s nullglob
    for file in "$directory"/*.png; do
        # Check if file is 1024x1024
        dimensions=$(identify -format "%wx%h" "$file" 2>/dev/null || echo "")
        if [[ "$dimensions" != "1024x1024" ]]; then
            log_warn "Skipping $file (not 1024x1024, got $dimensions)"
            continue
        fi

        base=$(basename "$file" .png)
        outdir="$directory/$base"
        mkdir -p "$outdir"

        log_info "Processing $file"

        cp "$file" "$outdir/${base}.png"
        convert "$file" -resize 512x512! "$outdir/${base}_512x512.png"
        convert "$file" -resize 256x256! "$outdir/${base}_256x256.png"
        convert "$file" -resize 128x128! "$outdir/${base}_128x128.png"

        icns_out="$directory/${base}.icns"
        png2icns "$icns_out" \
            "$outdir/${base}.png" \
            "$outdir/${base}_512x512.png" \
            "$outdir/${base}_256x256.png" \
            "$outdir/${base}_128x128.png"

        if [[ $? -eq 0 ]]; then
            log_success "Created $icns_out"
        else
            log_error "Failed to create $icns_out"
        fi
    done
    shopt -u nullglob
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
