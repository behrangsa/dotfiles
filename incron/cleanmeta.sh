#!/bin/bash

# cleanmeta.sh - Automated Image Metadata Cleaner
# Part of the dotfiles incron system for processing screenshots and browser captures
# Removes non-critical metadata while organizing files into date-based structures

set -euo pipefail

# Configuration
DEBUG_LOG="/tmp/cleanmeta.debug.log"
LOCK_DIR="/tmp/cleanmeta.locks"
MAX_LOCK_AGE=300  # 5 minutes

# Ensure lock directory exists
mkdir -p "$LOCK_DIR"

# Logging function
log_debug() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$DEBUG_LOG"
}

log_debug "=== Processing started for $* ==="

# Clean up old lock files
cleanup_old_locks() {
    log_debug "Cleaning up old lock files"
    find "$LOCK_DIR" -name "*.lock" -type f -mmin +$((MAX_LOCK_AGE / 60)) -delete 2>/dev/null || true
}

# Check if file is locked
is_locked() {
    local file="$1"
    local lock_file="$LOCK_DIR/$(basename "$file").lock"
    [[ -f "$lock_file" ]]
}

# Create lock file
create_lock() {
    log_debug "Creating lock for $1"
    local file="$1"
    local lock_file="$LOCK_DIR/$(basename "$file").lock"
    echo $$ > "$lock_file"
}

# Remove lock file
remove_lock() {
    log_debug "Removing lock for $1"
    local file="$1"
    local lock_file="$LOCK_DIR/$(basename "$file").lock"
    rm -f "$lock_file"
}

# Check dependencies
check_dependencies() {
    log_debug "Checking dependencies"
    local missing=()

    for cmd in exiftool pngcrush; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_debug "ERROR: Missing dependencies: ${missing[*]}"
        echo "Error: Missing required dependencies: ${missing[*]}" >&2
        echo "Install with: sudo apt install libimage-exiftool-perl pngcrush" >&2
        exit 1
    fi
}

# Detect file type
get_file_type() {
    local file="$1"
    local mime_type

    if command -v file >/dev/null 2>&1; then
        mime_type=$(file -b --mime-type "$file" 2>/dev/null)
        case "$mime_type" in
            image/jpeg) echo "jpeg" ;;
            image/png) echo "png" ;;
            *) echo "unknown" ;;
        esac
    else
        # Fallback to extension
        case "${file,,}" in
            *.jpg|*.jpeg) echo "jpeg" ;;
            *.png) echo "png" ;;
            *) echo "unknown" ;;
        esac
    fi
}

# Clean metadata from JPEG files
clean_jpeg_metadata() {
    local file="$1"
    local temp_file="${file}.tmp"

    log_debug "Cleaning JPEG metadata from: $file"

    # Use exiftool to remove all metadata except essential EXIF
    if exiftool -overwrite_original \
        -all= \
        -ColorSpace -ExifImageWidth -ExifImageHeight \
        -Orientation -XResolution -YResolution \
        -ResolutionUnit -YCbCrPositioning \
        "$file" 2>/dev/null; then
        log_debug "Successfully cleaned JPEG metadata: $file"
        return 0
    else
        log_debug "ERROR: Failed to clean JPEG metadata: $file"
        return 1
    fi
}

# Clean metadata from PNG files
clean_png_metadata() {
    local file="$1"
    local temp_file="${file}.tmp"

    log_debug "Cleaning PNG metadata from: $file"

    # Use pngcrush to remove textual metadata and optimize
    if pngcrush -rem tEXt -rem iTXt -rem zTXt -rem tIME -q \
        "$file" "$temp_file" 2>/dev/null; then
        mv "$temp_file" "$file"
        log_debug "Successfully cleaned PNG metadata: $file"
        return 0
    else
        rm -f "$temp_file"
        log_debug "ERROR: Failed to clean PNG metadata: $file"
        return 1
    fi
}

# Parse Ubuntu screenshot filename
parse_ubuntu_screenshot() {
    log_debug "Parsing Ubuntu screenshot filename: $1"
    local filename="$1"

    # Pattern: Screenshot from YYYY-MM-DD HH-MM-SS.ext
    if [[ "$filename" =~ ^Screenshot\ from\ ([0-9]{4})-([0-9]{2})-([0-9]{2})\ ([0-9]{2})-([0-9]{2})-([0-9]{2})\.(.+)$ ]]; then
        local year="${BASH_REMATCH[1]}"
        local month="${BASH_REMATCH[2]}"
        local day="${BASH_REMATCH[3]}"
        local hour="${BASH_REMATCH[4]}"
        local minute="${BASH_REMATCH[5]}"
        local second="${BASH_REMATCH[6]}"
        local extension="${BASH_REMATCH[7]}"

        echo "${year}/${month}/${day}/${year}-${month}-${day}_${hour}-${minute}-${second}_screenshot.ready.${extension}"
        return 0
    fi

    return 1
}

# Parse Vivaldi capture filename
parse_vivaldi_capture() {
    local filename="$1"

    # Pattern: YYYY-MM-DD HH.MM.SS domain.com alphanumeric.ext
    if [[ "$filename" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})\ ([0-9]{2})\.([0-9]{2})\.([0-9]{2})\ ([^\ ]+)\ [^\ ]+\.(.+)$ ]]; then
        local year="${BASH_REMATCH[1]}"
        local month="${BASH_REMATCH[2]}"
        local day="${BASH_REMATCH[3]}"
        local hour="${BASH_REMATCH[4]}"
        local minute="${BASH_REMATCH[5]}"
        local second="${BASH_REMATCH[6]}"
        local domain="${BASH_REMATCH[7]}"
        local extension="${BASH_REMATCH[8]}"

        echo "${year}/${month}/${day}/${year}-${month}-${day}_${hour}-${minute}-${second}_${domain}.ready.${extension}"
        return 0
    fi

    return 1
}

# Get target path for file
get_target_path() {
    local source_file="$1"
    local source_dir="$(dirname "$source_file")"
    local filename="$(basename "$source_file")"

    # Skip if already processed (has .ready extension)
    if [[ "$filename" == *.ready.* ]]; then
        log_debug "File already processed (has .ready extension): $filename"
        return 1
    fi

    # Determine base directory and pattern
    if [[ "$source_dir" == *"Screenshots"* ]]; then
        # Ubuntu Screenshot
        local relative_path
        if relative_path=$(parse_ubuntu_screenshot "$filename"); then
            echo "$source_dir/$relative_path"
            return 0
        fi
    elif [[ "$source_dir" == *"Vivaldi Captures"* ]] || [[ "$source_dir" == *"Vivaldi Screenshots"* ]] || [[ "$source_dir" == *".vivaldicaptures"* ]]; then
        # Vivaldi Capture
        local relative_path
        if relative_path=$(parse_vivaldi_capture "$filename"); then
            echo "$source_dir/$relative_path"
            return 0
        fi
    fi

    log_debug "No matching pattern found for: $filename in $source_dir"
    return 1
}

# Process a single file
process_file() {
    local source_file="$1"
    local debug_mode="${2:-false}"

    # Validate file exists and is readable
    if [[ ! -f "$source_file" ]] || [[ ! -r "$source_file" ]]; then
        log_debug "ERROR: File not found or not readable: $source_file"
        return 1
    fi

    # Check if file is locked
    if is_locked "$source_file"; then
        log_debug "File is locked, skipping: $source_file"
        return 1
    fi

    # Create lock
    create_lock "$source_file"

    # Ensure we remove the lock on exit
    trap "remove_lock '$source_file'" EXIT

    log_debug "Processing file: $source_file"

    # Get target path
    local target_path
    if ! target_path=$(get_target_path "$source_file"); then
        log_debug "Could not determine target path for: $source_file"
        return 1
    fi

    # Create target directory
    local target_dir="$(dirname "$target_path")"
    if ! mkdir -p "$target_dir"; then
        log_debug "ERROR: Failed to create target directory: $target_dir"
        return 1
    fi

    # Lock based rename to prevent re-triggering incron
    local temp_file="${source_file}.processing"
    create_lock "$temp_file"
    trap "remove_lock '$temp_file'" EXIT

    if ! mv "$source_file" "$temp_file"; then
        log_debug "ERROR: Failed to rename file for processing: $source_file"
        return 1
    fi

    # Determine file type and clean metadata
    local file_type
    file_type=$(get_file_type "$temp_file")

    case "$file_type" in
        jpeg)
            if ! clean_jpeg_metadata "$temp_file"; then
                log_debug "WARNING: Metadata cleaning failed for JPEG: $temp_file"
            fi
            ;;
        png)
            if ! clean_png_metadata "$temp_file"; then
                log_debug "WARNING: Metadata cleaning failed for PNG: $temp_file"
            fi
            ;;
        *)
            log_debug "WARNING: Unsupported file type ($file_type): $temp_file"
            ;;
    esac

    # Move to final location
    if mv "$temp_file" "$target_path"; then
        log_debug "SUCCESS: Processed and moved $source_file -> $target_path"

        if [[ "$debug_mode" == "true" ]]; then
            echo "Processed: $(basename "$source_file") -> $target_path"
        fi
    else
        log_debug "ERROR: Failed to move to target location: $temp_file -> $target_path"
        # Try to restore original file
        mv "$temp_file" "$source_file" 2>/dev/null || true
        return 1
    fi

    return 0
}

# Show help
show_help() {
    cat << 'EOF'
cleanmeta - Automated Image Metadata Cleaner

USAGE:
    cleanmeta [OPTIONS] FILE
    cleanmeta --help

DESCRIPTION:
    Processes image files to remove non-critical metadata and organize them
    into date-based directory structures. Designed for Ubuntu Screenshots
    and Vivaldi browser captures.

OPTIONS:
    --debug     Enable debug mode with verbose output
    --help      Show this help message

EXAMPLES:
    cleanmeta image.png
    cleanmeta --debug "Screenshot from 2025-06-03 18-50-40.png"

SUPPORTED PATTERNS:
    Ubuntu Screenshots:
        Screenshot from YYYY-MM-DD HH-MM-SS.ext

    Vivaldi Captures:
        YYYY-MM-DD HH.MM.SS domain.com alphanumeric.ext

DEPENDENCIES:
    - libimage-exiftool-perl (for JPEG metadata cleaning)
    - pngcrush (for PNG optimization and metadata removal)

FILES:
    Debug log: /tmp/cleanmeta.debug.log
    Lock files: /tmp/cleanmeta.locks/
EOF
}

# Main function
main() {
    local debug_mode=false
    local file_arg=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --debug)
                debug_mode=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            -*)
                echo "Error: Unknown option $1" >&2
                echo "Use --help for usage information." >&2
                exit 1
                ;;
            *)
                if [[ -n "$file_arg" ]]; then
                    echo "Error: Multiple file arguments not supported" >&2
                    exit 1
                fi
                file_arg="$1"
                shift
                ;;
        esac
    done

    # Check if file argument provided
    if [[ -z "$file_arg" ]]; then
        echo "Error: No file specified" >&2
        echo "Use --help for usage information." >&2
        exit 1
    fi

    # Initialize
    cleanup_old_locks
    check_dependencies

    # Log startup
    log_debug "=== cleanmeta.sh started (PID: $$) ==="
    log_debug "File: $file_arg"
    log_debug "Debug mode: $debug_mode"

    # Process the file
    if process_file "$file_arg" "$debug_mode"; then
        log_debug "=== Processing completed successfully ==="
        exit 0
    else
        log_debug "=== Processing failed ==="
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
