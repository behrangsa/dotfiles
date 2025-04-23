#!/bin/bash
#
# vim_tips_processor.sh
# 
# Purpose: Extract and format Vim tips from ~/.tippy/vim/latest.md for display in Conky
# Date: April 23, 2025
# 
# This script reads a markdown file containing Vim tips, extracts content up to 
# the "Explanation" section, and formats it for display in Conky.

# Enable strict error handling
set -eo pipefail

# Define log function for consistent error reporting
log_error() {
    echo "${CONKY_ERROR_COLOR}Error: $1${CONKY_RESET_FONT}" >&2
}

# Conky formatting variables
CONKY_TITLE_FONT='${color1}${font JetBrainsMono Nerd Font Mono:bold:size=14}'
CONKY_HEADING_FONT='${color2}${font JetBrainsMono Nerd Font Mono:bold:size=13}'
CONKY_SUBHEADING_FONT='${color}${font JetBrainsMono Nerd Font Mono:bold:size=12}'
CONKY_RESET_FONT='${font}${color}'
CONKY_ERROR_COLOR='${color3}'
CONKY_LIST_COLOR='${color white}'

# Path to the vim tips file (resolves symlinks automatically)
TIPS_FILE="$HOME/.tippy/vim/latest.md"

# Verify file exists and is readable
if [ ! -f "$TIPS_FILE" ]; then
    log_error "Vim tips file not found: $TIPS_FILE"
    exit 0
fi

if [ ! -r "$TIPS_FILE" ]; then
    log_error "Cannot read Vim tips file (check permissions): $TIPS_FILE"
    exit 0
fi

# Process the markdown file using awk for better control
awk -v heading_font="$CONKY_HEADING_FONT" \
    -v subheading_font="$CONKY_SUBHEADING_FONT" \
    -v reset_font="$CONKY_RESET_FONT" \
    -v list_color="$CONKY_LIST_COLOR" '
    BEGIN {
        # Flag to determine if we should continue processing
        keep_processing = 1
    }
    
    # Stop processing when we reach the Explanation section
    /^## Explanation/ {
        keep_processing = 0
        exit
    }
    
    # Process lines only if we should keep processing
    keep_processing == 1 {
        # Format H1 headings (e.g., "# Vim Tip #1")
        if ($0 ~ /^# /) {
            heading_text = substr($0, 3)  # Remove "# " prefix
            print heading_font heading_text reset_font
            # Always add a blank line after the main heading
            print ""
        }
        # Format H2 headings (e.g., "## Summary")
        else if ($0 ~ /^## /) {
            subheading_text = substr($0, 4)  # Remove "## " prefix
            print subheading_font subheading_text reset_font
        }
        # Format bullet points
        else if ($0 ~ /^- /) {
            print list_color $0
        }
        # Handle empty lines - preserve them
        else if ($0 ~ /^$/) {
            print ""
        }
        # Print other lines as is (paragraphs, etc.)
        else {
            print $0
        }
    }
' "$TIPS_FILE"