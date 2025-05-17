#!/usr/bin/env python3

import ollama
import argparse
import base64
import os
import re
import sys
import subprocess # For running exiftool
import shutil    # For checking if exiftool exists
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import time

# --- Configuration ---
OLLAMA_MODEL = "gemma3:latest"
# Formats generally known to support metadata (EXIF, IPTC, XMP) - used for filtering and warnings
# Keep lowercase for easier matching
METADATA_SUPPORTING_FORMATS_LOWER = {
    "jpeg", "jpg", "tiff", "tif", "png", "webp", "heif", "heic",
    "avif", "dng", "cr2", "nef", "arw", "orf", "pef", "rw2", "srw"
}
# --- End Configuration ---

def sanitize_filename(filename_base, extension):
    """Cleans a filename base and attaches the extension."""
    filename_base = filename_base.lower()
    filename_base = re.sub(r'[\s_-]+', '_', filename_base)
    # Allow alphanumeric, underscore, hyphen
    filename_base = re.sub(r'[^\w\-]+', '', filename_base)
    # Remove leading/trailing underscores/hyphens from the base name
    filename_base = filename_base.strip('_-')
    if not filename_base:
        filename_base = "image_analysis_result"
    # Limit base name length (optional, e.g., 100 chars)
    filename_base = filename_base[:100]
    # Ensure extension starts with a dot and is lowercase
    if extension and not extension.startswith('.'):
        extension = '.' + extension
    return f"{filename_base}{extension.lower()}"

def analyze_image_with_ollama(image_path):
    """
    Analyzes an image using Ollama and the specified model.
    Returns: (suggested_filename_base, suggested_description, suggested_labels_list, image_format)
             or (None, None, None, None) on failure.
    Filename base returned does NOT include the extension.
    """
    print(f"Analysing '{os.path.basename(image_path)}'...")
    abs_image_path = os.path.abspath(image_path)

    if not os.path.exists(abs_image_path):
        print(f"Error: Image file not found at '{abs_image_path}'", file=sys.stderr)
        return None, None, None, None

    image_format = None
    base64_image = None
    file_size = os.path.getsize(abs_image_path)
    print(f"File size: {file_size / 1024:.2f} KB")

    # Check for zero-byte file
    if file_size == 0:
        print("Error: Image file is empty (0 bytes). Skipping analysis.", file=sys.stderr)
        return None, None, None, None

    try:
        # 1. Open and identify image format
        with Image.open(abs_image_path) as img:
            image_format = img.format
            if not image_format:
                 print("Warning: Pillow could not detect image format directly.")
                 _, ext = os.path.splitext(abs_image_path)
                 image_format = ext.lstrip('.').upper() if ext else None
            print(f"Detected image format: {image_format or 'Unknown (using extension)'}")

            # 2. Read image bytes and encode to base64
            img_byte_arr = BytesIO()
            save_format = img.format # Try saving in original format
            if not save_format: # If Pillow didn't detect format, use extension or fallback
                _, ext = os.path.splitext(abs_image_path)
                save_format = ext.lstrip('.').upper()
                if not save_format:
                     save_format = 'PNG' # Ultimate fallback format

            try:
                # Convert before saving if necessary for the format (e.g. some formats need RGB)
                img_to_save = img
                if save_format == 'JPEG' and img.mode not in ('RGB', 'L'): # L is grayscale
                    print(f"Converting image mode from {img.mode} to RGB for JPEG saving.")
                    img_to_save = img.convert('RGB')
                elif save_format == 'PNG' and img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                    print(f"Converting image mode from {img.mode} to RGBA for PNG saving.")
                    img_to_save = img.convert('RGBA')

                img_to_save.save(img_byte_arr, format=save_format)
                print(f"Image data prepared using format: {save_format}")

            except Exception as save_err:
                 print(f"Warning: Could not save in format '{save_format}'. Trying PNG fallback. Error: {save_err}")
                 img_byte_arr = BytesIO() # Reset buffer
                 img_to_save = img
                 if img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                     print(f"Converting image mode from {img.mode} to RGBA for PNG analysis.")
                     img_to_save = img.convert('RGBA')
                 img_to_save.save(img_byte_arr, format='PNG')
                 print("Image data prepared using format: PNG")

            base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    except UnidentifiedImageError:
        print(f"Error: Pillow could not identify or open '{os.path.basename(image_path)}' as an image. Skipping.", file=sys.stderr)
        return None, None, None, None
    except Exception as e:
        print(f"Error opening/processing image with Pillow: {e}", file=sys.stderr)
        # Attempt fallback to reading raw bytes only if base64_image is still None
        if base64_image is None:
            print("Attempting fallback: Reading raw image bytes...")
            try:
                with open(abs_image_path, "rb") as f:
                    image_bytes = f.read()
                    if not image_bytes: # Double check if empty read
                        print("Error: Fallback failed, read 0 bytes.", file=sys.stderr)
                        return None, None, None, None
                    base64_image = base64.b64encode(image_bytes).decode('utf-8')
                _, ext = os.path.splitext(abs_image_path)
                image_format = ext.lstrip('.').upper() if ext else None
                print(f"Fallback successful. Using extension '{image_format or 'None'}' as format guess.")
            except Exception as fallback_e:
                 print(f"Fallback failed: Could not read raw image bytes: {fallback_e}", file=sys.stderr)
                 return None, None, None, None # Critical failure

    if base64_image is None:
         print("Error: Could not load image data for analysis.", file=sys.stderr)
         return None, None, None, image_format

    # 3. Prepare the prompt for Ollama
    prompt = """Analyze the provided image and suggest the following in a structured format:
1. A concise, descriptive filename suggestion (lowercase, use underscores instead of spaces, keep it relatively short, suitable for a file system, EXCLUDE the file extension).
2. A brief description sentence for the image (max 1-2 sentences).
3. A comma-separated list of relevant keywords or labels (5-10 labels, lowercase).

Use the following format exactly:
Filename: [your_suggested_filename_base_here]
Description: [Your suggested description here.]
Labels: [label1, label2, label3]
"""

    # 4. Call Ollama API
    try:
        print(f"Sending request to Ollama model '{OLLAMA_MODEL}'...")
        start_time = time.time()
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                    'images': [base64_image]
                }
            ]
        )
        analysis_text = response['message']['content']
        duration = time.time() - start_time
        print(f"Ollama analysis complete ({duration:.2f}s).")
        # print(f"--- Raw Ollama Response ---\n{analysis_text}\n--------------------------") # Debugging

    except Exception as e:
        print(f"\nError communicating with Ollama: {e}", file=sys.stderr)
        print(f"Ensure Ollama is running and the model '{OLLAMA_MODEL}' is available.", file=sys.stderr)
        return None, None, None, image_format

    # 5. Parse the response
    suggested_filename_base_raw = "unknown_image"
    suggested_description = "No description generated."
    suggested_labels_str = "No labels generated."

    try:
        lines = analysis_text.strip().split('\n')
        for line in lines:
            line_lower = line.lower()
            # Use partition for safer splitting
            if line_lower.startswith("filename:"):
                _, _, suggested_filename_base_raw = line.partition(":")
                suggested_filename_base_raw = suggested_filename_base_raw.strip()
            elif line_lower.startswith("description:"):
                _, _, suggested_description = line.partition(":")
                suggested_description = suggested_description.strip()
            elif line_lower.startswith("labels:"):
                _, _, suggested_labels_str = line.partition(":")
                suggested_labels_str = suggested_labels_str.strip()

        # Clean up labels
        labels_list = [label.strip().lower() for label in suggested_labels_str.split(',') if label.strip()]

        # Return the raw base filename (sanitization happens later with extension)
        return suggested_filename_base_raw, suggested_description, labels_list, image_format

    except Exception as e:
        print(f"\nError parsing Ollama response: {e}", file=sys.stderr)
        print("The model might not have followed the expected format.")
        print(f"--- Raw Ollama Response ---\n{analysis_text}\n--------------------------")
        return "analysis_failed", "Failed to parse description.", ["parsing_error"], image_format


def write_metadata_and_rename(original_path, new_filename_base, description, labels, image_format, force=False):
    """
    Writes metadata using exiftool and renames the file.

    Args:
        original_path (str): Absolute path to the original image file.
        new_filename_base (str): The suggested new filename base (without extension).
        description (str): The description to write.
        labels (list): A list of labels (keywords) to write.
        image_format (str): The detected image format (used for warning).
        force (bool): If True, skips safety checks like target file existing during rename.

    Returns:
        tuple: (bool, str) - (True if successful, new_path) or (False, original_path)
    """
    print("\n--- Applying Changes ---")
    abs_original_path = os.path.abspath(original_path)
    original_dir = os.path.dirname(abs_original_path)
    original_basename = os.path.basename(abs_original_path)
    _, original_ext = os.path.splitext(original_basename)

    # Sanitize and create the full new filename
    new_full_filename = sanitize_filename(new_filename_base, original_ext)
    new_path = os.path.join(original_dir, new_full_filename)

    # Check if exiftool is available
    exiftool_path = shutil.which("exiftool")
    if not exiftool_path:
        print("Error: 'exiftool' command not found. Cannot write metadata or rename.", file=sys.stderr)
        return False, abs_original_path # Indicate failure, return original path

    # Metadata writing part
    metadata_written = False
    cmd = [exiftool_path, "-overwrite_original", "-q"] # -q for quieter operation

    tags_to_write = []
    if description and description not in ("No description generated.", "Failed to parse description."):
        tags_to_write.append(f"-XMP-dc:Description={description}")
        tags_to_write.append(f"-IPTC:Caption-Abstract={description}")

    if labels and labels != ["parsing_error"] and labels != ["No labels generated."]:
        # Check existing tags first if needed or just overwrite
        tags_to_write.append("-Subject=") # Clear existing subjects/keywords
        for label in labels:
            tags_to_write.append(f"-Subject={label}") # Add each new label

    if tags_to_write:
        cmd.extend(tags_to_write)
        cmd.append(abs_original_path)

        print(f"Running exiftool to write metadata to '{original_basename}'...")
        try:
            # Add - L to allow non-english chars in tags
            env = os.environ.copy()
            env['EXIFTOOL_CHARSET'] = 'UTF8' # Recommended for exiftool with unicode
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
            print("Exiftool metadata write successful.")
            metadata_written = True # Mark as success
            if result.stderr.strip(): # Show exiftool warnings even with -q
                 print(f"Exiftool warnings:\n{result.stderr.strip()}", file=sys.stderr)

        except subprocess.CalledProcessError as e:
            print(f"Error running exiftool: {e}", file=sys.stderr)
            print(f"Command: {' '.join(e.cmd)}", file=sys.stderr)
            print(f"Return Code: {e.returncode}", file=sys.stderr)
            print(f"Output:\n{e.stdout}", file=sys.stderr)
            print(f"Error Output:\n{e.stderr}", file=sys.stderr)
            print("Metadata writing failed. Proceeding with rename attempt if applicable.")
            # Do not return yet, allow rename attempt if filename changed
        except Exception as e:
            print(f"An unexpected error occurred while running exiftool: {e}", file=sys.stderr)
            print("Metadata writing failed. Proceeding with rename attempt if applicable.")
    else:
        print("No valid metadata suggestions to write.")
        metadata_written = True # No data to write counts as 'success' for this step


    # Renaming part
    if abs_original_path == new_path:
        print(f"Suggested filename '{new_full_filename}' is the same as the original. Skipping rename.")
        # If metadata write failed previously, the overall operation failed.
        # If metadata write succeeded (or was skipped), the operation succeeded.
        return metadata_written, abs_original_path

    rename_succeeded = False
    print(f"Attempting rename: '{original_basename}' -> '{new_full_filename}'")
    try:
        if os.path.exists(new_path):
            if force:
                 print(f"Warning: Target file '{new_path}' already exists. Forcing rename (will overwrite!).")
                 os.remove(new_path)
                 print(f"Removed existing file: '{new_path}'")
            else:
                print(f"Error: Target filename '{new_path}' already exists. Rename aborted.", file=sys.stderr)
                print("Use --force to overwrite.")
                # Even if rename failed, if metadata was written, return success but the *original* path
                return metadata_written, abs_original_path

        os.rename(abs_original_path, new_path)
        print("Rename successful.")
        rename_succeeded = True
        # If rename succeeded, return the new path. Success status depends on both steps.
        return metadata_written and rename_succeeded, new_path

    except OSError as e:
        print(f"Error renaming file: {e}", file=sys.stderr)
        # If rename fails, the overall operation failed. Return original path.
        return False, abs_original_path
    except Exception as e:
        print(f"An unexpected error occurred during rename: {e}", file=sys.stderr)
        return False, abs_original_path

# --- Function to process a single file ---
def process_single_file(file_path, write_changes, force_write):
    """Analyzes and optionally modifies a single image file."""
    print(f"\n--- Processing File: {file_path} ---")
    success = False
    final_path = file_path # Keep track of the file's potentially new path

    # 1. Analyze
    filename_base, description, labels, img_format = analyze_image_with_ollama(file_path)

    if filename_base is None: # Analysis failed critically
        print(f"Analysis failed for {file_path}. Skipping further actions.")
        return False, final_path # Indicate failure

    # Get original extension to build the full suggested filename
    _, original_ext = os.path.splitext(file_path)
    suggested_full_filename = sanitize_filename(filename_base, original_ext)

    # 2. Print Suggestions
    print("\n--- Suggestions ---")
    print(f"Suggested Filename : {suggested_full_filename}")
    print(f"Suggested Desc.    : {description}")
    print(f"Suggested Labels   : {', '.join(labels)}")
    print(f"Detected Format    : {img_format or 'Unknown'}")

    # 3. Write changes if requested
    if write_changes:
        # Pass the *base* filename suggestion to the write function
        write_success, final_path = write_metadata_and_rename(
            file_path, # Pass the current path of the file
            filename_base, # Pass only the base name suggestion
            description,
            labels,
            img_format,
            force=force_write
        )
        success = write_success # Overall success depends on the write/rename step
    else:
        print("\nRun with -w (prompt) or -f (force) to apply these changes (requires exiftool).")
        success = True # Analysis succeeded, no write requested, so count as success

    print(f"--- Finished Processing: {os.path.basename(final_path)} ---")
    return success, final_path


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Suggest filename and metadata for images using Ollama ({OLLAMA_MODEL}). Processes a single file or a directory.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_path", help="Path to the image file or a directory containing images.")
    parser.add_argument(
        "-w", "--write",
        action="store_true",
        help="Write metadata and rename file(s). Requires 'exiftool'. Prompts for confirmation (unless -f is used)."
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force write/rename without confirmation. Implies -w. Overwrites existing target files during rename. *** Use with extreme caution! ***"
    )
    args = parser.parse_args()

    abs_input_path = os.path.abspath(args.input_path)
    files_to_process = []
    is_dir = False

    # Check if input is file or directory
    if os.path.isfile(abs_input_path):
        # Check if the single file is supported
        _, ext = os.path.splitext(abs_input_path)
        if ext.lstrip('.').lower() in METADATA_SUPPORTING_FORMATS_LOWER:
            files_to_process.append(abs_input_path)
        else:
             print(f"Error: Input file '{abs_input_path}' does not have a supported extension ({', '.join(METADATA_SUPPORTING_FORMATS_LOWER)}).", file=sys.stderr)
             sys.exit(1)

    elif os.path.isdir(abs_input_path):
        is_dir = True
        print(f"Scanning directory: {abs_input_path}")
        found_count = 0
        for item in os.listdir(abs_input_path):
            item_path = os.path.join(abs_input_path, item)
            if os.path.isfile(item_path):
                _, ext = os.path.splitext(item)
                if ext.lstrip('.').lower() in METADATA_SUPPORTING_FORMATS_LOWER:
                    files_to_process.append(item_path)
                    found_count += 1
        print(f"Found {found_count} supported image files.")
        if not files_to_process:
            print("No supported image files found in the directory.")
            sys.exit(0)

    else:
        print(f"Error: Input path '{abs_input_path}' is not a valid file or directory.", file=sys.stderr)
        sys.exit(1)

    # Determine if writing should happen
    should_write = args.write or args.force
    proceed_with_write = False

    # Confirmation for batch write (if directory and -w without -f)
    if should_write and not args.force:
        print("\n*** WARNING: You requested to write changes! ***")
        if is_dir:
            print(f"This will attempt to modify {len(files_to_process)} file(s) in '{abs_input_path}'.")
            print("Metadata will be written and files may be RENAMED.")
            print("Existing files with the *new suggested name* will cause an error unless --force is used.")
        else:
            # Single file confirmation message (similar to before)
            print(f"  - Metadata will be written to: '{os.path.basename(files_to_process[0])}'")
            # Simulating potential rename for confirmation message
            # Note: This is a guess, actual analysis is needed for real suggested name
            print(f"  - File may be RENAMED based on analysis.")
            print("  - Existing files with the new name will cause an error unless --force is used.")

        confirm = input("Proceed with writing changes? (yes/no): ").strip().lower()
        if confirm == 'yes':
            proceed_with_write = True
        else:
            print("Write operation cancelled by user.")
            # If cancelled, treat as if -w was not provided
            should_write = False
    elif args.force:
        print("\n*** WARNING: --force specified! Applying changes WITHOUT confirmation! ***")
        print("***          Existing target files during rename WILL BE OVERWRITTEN! ***")
        proceed_with_write = True


    # Process the files
    total_files = len(files_to_process)
    success_count = 0
    fail_count = 0

    for i, file_path in enumerate(files_to_process):
        if is_dir:
             print(f"\n{'='*10} Processing file {i+1} of {total_files} {'='*10}")

        # Pass should_write AND proceed_with_write status
        # process_single_file decides whether to call write_metadata based on this
        write_this_file = should_write and proceed_with_write
        file_success, _ = process_single_file(file_path, write_this_file, args.force)

        if file_success:
            success_count += 1
        else:
            fail_count += 1

    # Final Summary
    print("\n" + "="*30)
    print("Processing Complete.")
    print(f"Total files processed: {total_files}")
    print(f"Successful: {success_count}")
    print(f"Failed:     {fail_count}")
    print("="*30)

    if fail_count > 0:
        sys.exit(1) # Exit with error code if any file failed
    else:
        sys.exit(0)

