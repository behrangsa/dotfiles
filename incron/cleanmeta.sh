#!/bin/bash

# cleanmeta.sh - A utility to clean non-critical metadata from image files
#
# This script is triggered by incron whenever a new image file is saved
# in the `$USER_HOME/Pictures/Screenshots` directory. It removes non-critical
# metadata from JPEG and PNG files using `exiftool` and `pngcrush`, respectively.

set -euo pipefail

# Lock file to prevent multiple instances
LOCK_FILE="/tmp/cleanmeta.lock"

# Debug log file
DEBUG_LOG="/tmp/cleanmeta.debug.log"

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    local msg="[INFO] $1"
    echo -e "${BLUE}${msg}${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') ${msg}" >> "$DEBUG_LOG"
}

log_success() {
    local msg="[SUCCESS] $1"
    echo -e "${GREEN}${msg}${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') ${msg}" >> "$DEBUG_LOG"
}

log_warn() {
    local msg="[WARNING] $1"
    echo -e "${YELLOW}${msg}${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') ${msg}" >> "$DEBUG_LOG"
}

log_error() {
    local msg="[ERROR] $1"
    echo -e "${RED}${msg}${NC}" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') ${msg}" >> "$DEBUG_LOG"
}

# Function to clean JPEG metadata
clean_jpeg() {
    local file="$1"
    local new_file
    new_file=$(format_filename "$file" "jpg" 2>/dev/null)

    # Create directory structure
    mkdir -p "$(dirname "$new_file")"

    mv "$file" "$new_file"
    log_info "Renamed and moved file to: $new_file"
    if exiftool -all= -tagsfromfile @ -exif:all "$new_file" -overwrite_original > /dev/null 2>&1; then
        log_success "Metadata cleaned successfully for: $new_file"
    else
        log_error "Failed to clean metadata for: $new_file"
        return 1
    fi
}

# Function to clean PNG metadata
clean_png() {
    local file="$1"
    local new_file
    new_file=$(format_filename "$file" "png" 2>/dev/null)

    # Create directory structure
    mkdir -p "$(dirname "$new_file")"

    mv "$file" "$new_file"
    log_info "Renamed and moved file to: $new_file"
    if pngcrush -rem text -rem time -reduce -brute -ow "$new_file" > /dev/null 2>&1; then
        log_success "Metadata cleaned successfully for: $new_file"
    else
        log_error "Failed to clean metadata for: $new_file"
        return 1
    fi
}

# Function to format filename and create date-based directory structure
format_filename() {
    local file="$1"
    local extension="$2"
    local base_name=$(basename "$file")
    local dir_name=$(dirname "$file")

    # Extract date and time from screenshot filename
    log_info "Processing filename: '$base_name'" >&2
    if [[ "$base_name" =~ Screenshot\ from\ ([0-9]{4})-([0-9]{2})-([0-9]{2})\ ([0-9]{2})-([0-9]{2})-([0-9]{2}) ]]; then
        local year="${BASH_REMATCH[1]}"
        local month="${BASH_REMATCH[2]}"
        local day="${BASH_REMATCH[3]}"
        local hour="${BASH_REMATCH[4]}"
        local minute="${BASH_REMATCH[5]}"
        local second="${BASH_REMATCH[6]}"

        # Create formatted filename: date_time_screenshot.ready.ext
        local formatted_name="${year}-${month}-${day}_${hour}-${minute}-${second}_screenshot.ready.${extension}"

        # Convert to lowercase and replace spaces with underscores
        formatted_name=$(echo "$formatted_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')

        # Create date-based directory structure
        local target_dir="${year}/${month}/${day}"
        log_info "Generated target directory: '$target_dir'" >&2
        log_info "Generated filename: '$formatted_name'" >&2

        echo "${target_dir}/${formatted_name}"
    elif [[ "$base_name" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})\ ([0-9]{2})\.([0-9]{2})\.([0-9]{2})\ ([^\ ]+)\ [a-zA-Z0-9]+\.(png|jpg|jpeg)$ ]]; then
        # Vivaldi Captures pattern: YYYY-MM-DD HH.MM.SS domain_name alphanumeric.ext
        local year="${BASH_REMATCH[1]}"
        local month="${BASH_REMATCH[2]}"
        local day="${BASH_REMATCH[3]}"
        local hour="${BASH_REMATCH[4]}"
        local minute="${BASH_REMATCH[5]}"
        local second="${BASH_REMATCH[6]}"
        local domain="${BASH_REMATCH[7]}"

        # Create formatted filename: date-time_domain.ready.ext (replace . with - in time)
        local formatted_name="${year}-${month}-${day}_${hour}-${minute}-${second}_${domain}.ready.${extension}"

        # Convert to lowercase and replace spaces with underscores
        formatted_name=$(echo "$formatted_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')

        # Create date-based directory structure
        local target_dir="${year}/${month}/${day}"
        log_info "Generated target directory: '$target_dir'" >&2
        log_info "Generated filename: '$formatted_name'" >&2

        echo "${target_dir}/${formatted_name}"
    else
        # Fallback for non-screenshot files
        log_warn "Filename doesn't match Ubuntu Screenshot or Vivaldi Capture pattern, using fallback" >&2
        local name="${base_name%.*}"
        local formatted_name=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | sed 's/from_//g')
        log_info "Fallback filename: '${formatted_name}.ready.${extension}'" >&2
        echo "${formatted_name}.ready.${extension}"
    fi
}

# Function to check if required tools are available
check_dependencies() {
    local missing_tools=()

    if ! command -v exiftool &> /dev/null; then
        missing_tools+=("exiftool")
    fi

    if ! command -v pngcrush &> /dev/null; then
        missing_tools+=("pngcrush")
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again"
        exit 1
    fi
}

# Main function
main() {
    local file="$1"

    # Log the original argument for debugging
    log_info "Raw file argument: '$file'"

    # Handle filename with spaces - remove any trailing characters after the extension
    if [[ "$file" =~ (.+\.(png|jpg|jpeg)).*$ ]]; then
        file="${BASH_REMATCH[1]}"
        log_info "Cleaned file path: '$file'"
    fi

    # Check if the file exists
    if [ ! -f "$file" ]; then
        log_error "File does not exist: $file"
        exit 1
    fi

    # Ignore files with .ready extensions
    if [[ "$file" =~ \.ready\.(png|jpg|jpeg)$ ]]; then
        log_info "Ignoring file with .ready extension: $file"
        exit 0
    fi

    # Check dependencies
    check_dependencies

    # Prevent multiple instances using a lock file
    if [ -f "$LOCK_FILE" ]; then
        log_warn "Script is already running. Exiting to prevent infinite loop."
        exit 0
    fi
    touch "$LOCK_FILE"
    trap "rm -f $LOCK_FILE" EXIT

    # Log the file being processed for debugging
    log_info "Processing file: $file"

    # Determine file type and clean metadata
    case "${file,,}" in
        *.jpg|*.jpeg)
            clean_jpeg "$file"
            ;;
        *.png)
            clean_png "$file"
            ;;
        *)
            log_warn "Unsupported file type: $file"
            exit 0
            ;;
    esac
}

# Show usage information
show_usage() {
    echo "Usage: $(basename "$0") [OPTIONS] <file>"
    echo ""
    echo "Clean non-critical metadata from image files."
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message and exit"
    echo "  -d, --debug    Enable verbose debug output"
    echo ""
    echo "Arguments:"
    echo "  <file>         Path to the image file to process"
    echo ""
    echo "Supported formats: PNG, JPG, JPEG"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0") screenshot.png"
    echo "  $(basename "$0") --debug photo.jpg"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Initialize debug log
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SCRIPT START] $0 $*" >> "$DEBUG_LOG"

    # Parse command line arguments
    DEBUG_MODE=false
    FILE_ARG=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--debug)
                DEBUG_MODE=true
                ;;
            -*)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
            *)
                if [[ -z "$FILE_ARG" ]]; then
                    FILE_ARG="$1"
                else
                    log_error "Too many arguments"
                    show_usage
                    exit 1
                fi
                ;;
        esac
        shift
    done

    if [[ -z "$FILE_ARG" ]]; then
        log_error "No file specified"
        show_usage
        exit 1
    fi

    if [[ "$DEBUG_MODE" == "true" ]]; then
        log_info "Debug mode enabled"
        log_info "Debug log: $DEBUG_LOG"
        log_info "Raw arguments received: $@"
        log_info "Processed file argument: '$FILE_ARG'"
    fi

    main "$FILE_ARG"
fi
