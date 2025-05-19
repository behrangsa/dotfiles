#!/usr/bin/env bash
set -Eeuo pipefail # Strict mode: exit on error, unset var, pipefail; ERR traps inherited

# --- Script metadata ---
SCRIPT_NAME="imgls"
SCRIPT_VERSION="1.6.0"
SCRIPT_DESCRIPTION="Displays images in a grid, with pagination and title trimming."

# --- Global Constants and Configuration ---
INTER_IMAGE_PADDING=2       # Visual space between image cells
IMG_DISPLAY_HEIGHT_CELLS=10 # Desired height of images in terminal cells
TITLE_DISPLAY_LINES=1       # Lines reserved for filename display
INTER_ROW_SPACING_LINES=1   # Blank lines between titles of one row and images of the next
ELLIPSIS=$'\u2026'          # Unicode ellipsis character …
MAX_NAME_PART_LEN_FOR_ELLIPSIS=8 # If name (pre-extension) > this, apply ellipsis logic
ELLIPSIS_PREFIX_LEN=4       # e.g., "josh"
ELLIPSIS_SUFFIX_LEN=3       # e.g., "ash"

# --- Function Definitions ---
cleanup() {
    tput cnorm || true # Restore cursor visibility
}

check_dependencies() {
    local missing_deps=0
    for cmd in "kitty" "tput" "basename"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo "Error: Required command '$cmd' not found in PATH." >&2
            missing_deps=1
        fi
    done
    if [ "$missing_deps" -eq 1 ]; then
        exit 2
    fi
}

# --- Main Application Logic ---
main() {
    local cols=${1:-3} # Default to 3 columns, or use first argument
    if ! [[ "$cols" =~ ^[1-9][0-9]*$ ]]; then
        echo "Usage: $SCRIPT_NAME [number_of_columns (default: 3)]" >&2
        echo "Error: Number of columns must be a positive integer." >&2
        exit 1
    fi

    local term_width term_height
    term_width=$(tput cols)
    term_height=$(tput lines)

    if ! [[ "$term_width" =~ ^[0-9]+$ && "$term_height" =~ ^[0-9]+$ ]]; then
        echo "Error: Could not determine terminal dimensions via tput." >&2; exit 1; fi
    if [ "$term_width" -le 0 ] || [ "$term_height" -le 0 ]; then
        echo "Error: Invalid terminal dimensions reported by tput ($term_width x $term_height)." >&2; exit 1; fi

    local slot_width_per_col=$((term_width / cols))
    if [ "$slot_width_per_col" -lt 1 ]; then
        echo "Error: Terminal width ($term_width) is too narrow for $cols columns." >&2; exit 1; fi

    local img_display_width_cells # This is the max width for image AND title in a cell
    if [ "$slot_width_per_col" -le "$INTER_IMAGE_PADDING" ]; then
        img_display_width_cells=$slot_width_per_col
    else
        img_display_width_cells=$((slot_width_per_col - INTER_IMAGE_PADDING))
    fi
    [ "$img_display_width_cells" -lt 1 ] && img_display_width_cells=1

    local row_block_total_height=$((IMG_DISPLAY_HEIGHT_CELLS + TITLE_DISPLAY_LINES + INTER_ROW_SPACING_LINES))
    if [ "$row_block_total_height" -gt "$term_height" ]; then
        echo "Error: Terminal height ($term_height lines) is insufficient to display even one row of images" >&2
        echo "       (needs $row_block_total_height lines per image row block)." >&2
        exit 1
    fi

    shopt -s nullglob
    local image_files=(*.jpg *.jpeg *.png *.gif *.webp *.avif) # Added .avif
    shopt -u nullglob

    if [ ${#image_files[@]} -eq 0 ]; then
        echo "No compatible images found in the current directory." >&2
        return 0
    fi

    clear; printf "\033[H"; tput civis

    local master_img_idx=0
    local page_images_processed_this_block=0
    local filenames_for_current_row=()

    while [ "$master_img_idx" -lt "${#image_files[@]}" ]; do
        local current_col_in_row_on_page=$((page_images_processed_this_block % cols))
        local current_logical_row_idx_on_page=$((page_images_processed_this_block / cols))

        if [ "$current_col_in_row_on_page" -eq 0 ] && \
           [ $((current_logical_row_idx_on_page * row_block_total_height + row_block_total_height)) -gt "$term_height" ]; then
            local user_input
            printf "\033[%d;1H\033[K" "$term_height"
            read -n 1 -s -r -p "Page full. Press any key for next page, or Q to quit... " user_input
            printf "\r\033[K"
            if [[ "$user_input" == "q" || "$user_input" == "Q" ]]; then
                printf "\033[%d;1H\n" "$term_height"; exit 0; fi
            clear; page_images_processed_this_block=0
            current_col_in_row_on_page=0; current_logical_row_idx_on_page=0
        fi

        local img_path="${image_files[$master_img_idx]}"
        local x_pos_slot_cells=$((current_col_in_row_on_page * slot_width_per_col))
        local y_pos_cells=$((current_logical_row_idx_on_page * row_block_total_height))

        local W="$img_display_width_cells" H="$IMG_DISPLAY_HEIGHT_CELLS" X="$x_pos_slot_cells" Y="$y_pos_cells"
        if ! [[ "$W" =~ ^[0-9]+$ && "$H" =~ ^[0-9]+$ && "$X" =~ ^[0-9]+$ && "$Y" =~ ^[0-9]+$ ]]; then
            echo "Error: Internal script error - Invalid geometric args for '$img_path'." >&2
            echo "Details: W='$W', H='$H', X='$X', Y='$Y'" >&2; exit 3;
        fi
        local place_arg="${W}x${H}@${X}x${Y}"

        local icat_success=true
        set +e
        command kitty +kitten icat --silent --place="$place_arg" "$img_path"
        local icat_exit_code=$?
        set -e

        if [ "$icat_exit_code" -ne 0 ]; then
            icat_success=false
            local err_msg_line=$((y_pos_cells + H / 2)); [ "$err_msg_line" -le 0 ] && err_msg_line=1
            [ "$err_msg_line" -gt "$term_height" ] && err_msg_line=$term_height
            printf "\033[%d;%dH\033[K" "$err_msg_line" "$X"
            printf "%-*.*s" "$W" "$W" "[ERR:$icat_exit_code Disp Fail]"
            local user_input_err
            printf "\033[%d;1H\033[K" "$term_height"
            read -n 1 -s -r -p "Failed to display '$img_path'. Continue (c/any key) or Quit (q)? " user_input_err
            printf "\r\033[K"
            if [[ "$user_input_err" == "q" || "$user_input_err" == "Q" ]]; then
                 printf "\033[%d;1H\n" "$term_height"; exit 6; fi
        fi

        # --- Title Generation with Trimming ---
        local base_filename=$(basename "$img_path")
        local name_part_raw="$base_filename"
        local extension_raw=""

        if [[ "$base_filename" == *.* ]]; then # Check if there's any dot for extension
            extension_raw="${base_filename##*.}" # Capture part after the last dot
            name_part_raw="${base_filename%.*}"   # Capture part before the last dot

            # If name_part_raw is empty AND original filename started with a dot (e.g. ".bashrc")
            # treat the whole thing as the name part, and no extension.
            if [[ -z "$name_part_raw" ]] && [[ "$base_filename" == .* ]]; then
                name_part_raw="$base_filename"
                extension_raw=""
            else
                # Prepend the dot back to the extension if it's not empty
                [ -n "$extension_raw" ] && extension_raw=".$extension_raw"
            fi
        fi

        local final_name_for_display="$name_part_raw"
        if ((${#name_part_raw} > MAX_NAME_PART_LEN_FOR_ELLIPSIS)); then
            local prefix="${name_part_raw:0:$ELLIPSIS_PREFIX_LEN}"
            local suffix="${name_part_raw: -$ELLIPSIS_SUFFIX_LEN}"
            final_name_for_display="${prefix}${ELLIPSIS}${suffix}"
        fi
        local title_before_cell_limit="${final_name_for_display}${extension_raw}"

        local final_display_title
        printf -v final_display_title "%.*s" "$img_display_width_cells" "$title_before_cell_limit"

        if [ "$icat_success" = true ]; then
            filenames_for_current_row[$current_col_in_row_on_page]="$final_display_title"
        else
            filenames_for_current_row[$current_col_in_row_on_page]="[$final_display_title]" # Mark error
        fi
        # --- End Title Generation ---

        master_img_idx=$((master_img_idx + 1))
        page_images_processed_this_block=$((page_images_processed_this_block + 1))

        local is_last_col_on_page=$(((page_images_processed_this_block % cols) == 0))
        local is_last_image_overall=$((master_img_idx == ${#image_files[@]}))

        if [ "$is_last_col_on_page" -eq 1 ] || [ "$is_last_image_overall" -eq 1 ]; then
            if [ ${#filenames_for_current_row[@]} -gt 0 ]; then
                local title_line_on_screen=$((y_pos_cells + IMG_DISPLAY_HEIGHT_CELLS + 1))
                if [ "$title_line_on_screen" -le "$term_height" ]; then
                    printf "\033[%d;1H" "$title_line_on_screen"
                    for ((i=0; i<cols; i++)); do
                        local title_x_char_pos=$((i * slot_width_per_col + 1))
                        local title_to_print="${filenames_for_current_row[$i]:-}"
                        if [ -z "$title_to_print" ] && [ "$i" -lt "${#filenames_for_current_row[@]}" ]; then
                             # This case should ideally not happen if placeholders are used for empty slots due to skip
                             # If an image was skipped, its slot in filenames_for_current_row might be empty
                             # or we ensure a placeholder like "[skipped]" or "[error]" is there.
                             # The current logic puts "[title]" for error or the actual title.
                             # To ensure alignment, print spaces if title_to_print is truly empty for a processed slot.
                            printf "\033[%dG%*s" "$title_x_char_pos" "$img_display_width_cells" ""
                        else
                             printf "\033[%dG%-*.*s" "$title_x_char_pos" \
                                "$img_display_width_cells" "$img_display_width_cells" \
                                "$title_to_print"
                        fi
                    done
                    printf "\n"
                fi
            fi
            filenames_for_current_row=()
        fi
    done

    local num_rows_on_last_page=$(( (page_images_processed_this_block + cols - 1) / cols ))
    local final_content_end_y
    if [ "$page_images_processed_this_block" -eq 0 ]; then final_content_end_y=0
    else final_content_end_y=$((num_rows_on_last_page * row_block_total_height)); fi
    local final_cursor_line_pos=$((final_content_end_y + 1))
    [ "$final_cursor_line_pos" -gt "$term_height" ] && final_cursor_line_pos=$term_height
    [ "$final_cursor_line_pos" -le 0 ] && final_cursor_line_pos=1
    printf "\033[%d;1H" "$final_cursor_line_pos"
    printf "\033[K\n"
}

trap cleanup EXIT SIGINT SIGTERM
check_dependencies
main "$@"
