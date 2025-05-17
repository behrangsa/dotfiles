#!/usr/bin/env python3

"""
ImgTag - AI-powered image tagging, metadata enrichment, and smart renaming utility.

This script uses Ollama API to analyze images and generate appropriate filenames,
descriptions, and tags based on image content. It can also write metadata to image
files and rename them according to AI suggestions.
"""

import ollama
import argparse
import base64
import os
import re
import sys
import subprocess # For running exiftool
import shutil     # For checking if exiftool exists
from typing import List, Tuple, Optional, Set
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import time

# --- Configuration ---
OLLAMA_MODEL = "gemma3:latest"
# Formats generally known to support metadata (EXIF, IPTC, XMP) - used for filtering and warnings
# Keep lowercase for easier matching
METADATA_SUPPORTING_FORMATS_LOWER: Set[str] = {
    "jpeg", "jpg", "tiff", "tif", "png", "webp", "heif", "heic",
    "avif", "dng", "cr2", "nef", "arw", "orf", "pef", "rw2", "srw"
}
# --- End Configuration ---

def setup_logging() -> None:
    """Configure basic logging (placeholder for future logging implementation)."""
    pass # In future could use logging module instead of print

def sanitize_filename(filename_base: str, extension: str) -> str:
    """
    Cleans a filename base and attaches the extension.
    
    Args:
        filename_base: The base filename to sanitize
        extension: The file extension (with or without leading dot)
        
    Returns:
        A sanitized filename with extension
    """
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

def prepare_image_data(image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Prepares image data for analysis by converting to base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple containing (base64_encoded_image, image_format)
        Both can be None if processing fails
    """
    # Early validation
    if not image_path or not isinstance(image_path, str):
        print("Error: Invalid image path provided", file=sys.stderr)
        return None, None
        
    # Validate file exists
    abs_image_path = os.path.abspath(image_path)
    if not os.path.exists(abs_image_path):
        print(f"Error: Image file not found at '{abs_image_path}'", file=sys.stderr)
        return None, None

    # Check file size
    file_size = os.path.getsize(abs_image_path)
    print(f"File size: {file_size / 1024:.2f} KB")
    if file_size == 0:
        print("Error: Image file is empty (0 bytes). Skipping analysis.", file=sys.stderr)
        return None, None

    # First try using PIL
    result = _prepare_with_pil(abs_image_path)
    if result[0] is not None:
        return result
        
    # Fall back to raw bytes if PIL fails
    return _prepare_with_raw_bytes(abs_image_path)

def _prepare_with_pil(abs_image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Helper function for PIL-based image processing"""
    try:
        with Image.open(abs_image_path) as img:
            # Get format
            image_format = img.format
            if not image_format:
                print("Warning: Pillow could not detect image format directly.")
                _, ext = os.path.splitext(abs_image_path)
                image_format = ext.lstrip('.').upper() if ext else None
            print(f"Detected image format: {image_format or 'Unknown (using extension)'}")

            # Determine save format
            save_format = img.format
            if not save_format:
                _, ext = os.path.splitext(abs_image_path)
                save_format = ext.lstrip('.').upper()
                if not save_format:
                    save_format = 'PNG'

            return _save_image_to_base64(img, save_format)
            
    except UnidentifiedImageError:
        print(f"Error: Pillow could not identify or open '{os.path.basename(abs_image_path)}' as an image.", 
              file=sys.stderr)
        return None, None
        
    except Exception as e:
        print(f"Error opening/processing image with Pillow: {e}", file=sys.stderr)
        return None, None

def _save_image_to_base64(img: Image.Image, save_format: str) -> Tuple[Optional[str], Optional[str]]:
    """Helper function to save image to base64 with proper format conversion"""
    try:
        img_byte_arr = BytesIO()
        img_to_save = img
        
        # Convert image mode if needed for the target format
        if save_format == 'JPEG' and img.mode not in ('RGB', 'L'):
            print(f"Converting image mode from {img.mode} to RGB for JPEG saving.")
            img_to_save = img.convert('RGB')
        elif save_format == 'PNG' and img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
            print(f"Converting image mode from {img.mode} to RGBA for PNG analysis.")
            img_to_save = img.convert('RGBA')

        img_to_save.save(img_byte_arr, format=save_format)
        print(f"Image data prepared using format: {save_format}")
        base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        return base64_image, save_format
        
    except Exception as save_err:
        # Try PNG as fallback
        print(f"Warning: Could not save in format '{save_format}'. Trying PNG fallback. Error: {save_err}")
        try:
            img_byte_arr = BytesIO()
            img_to_save = img
            if img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                print(f"Converting image mode from {img.mode} to RGBA for PNG analysis.")
                img_to_save = img.convert('RGBA')
                
            img_to_save.save(img_byte_arr, format='PNG')
            print("Image data prepared using format: PNG")
            base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            return base64_image, 'PNG'
        except Exception as e:
            print(f"Error in PNG fallback: {e}", file=sys.stderr)
            return None, None

def _prepare_with_raw_bytes(abs_image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """Helper function for raw bytes fallback"""
    print("Attempting fallback: Reading raw image bytes...")
    try:
        with open(abs_image_path, "rb") as f:
            image_bytes = f.read()
            if not image_bytes:
                print("Error: Fallback failed, read 0 bytes.", file=sys.stderr)
                return None, None
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
        _, ext = os.path.splitext(abs_image_path)
        image_format = ext.lstrip('.').upper() if ext else None
        print(f"Fallback successful. Using extension '{image_format or 'None'}' as format guess.")
        return base64_image, image_format
    except Exception as fallback_e:
        print(f"Fallback failed: Could not read raw image bytes: {fallback_e}", file=sys.stderr)
        return None, None

def call_ollama_api(base64_image: str) -> Optional[str]:
    """
    Calls Ollama API to analyze the image.
    
    Args:
        base64_image: Base64-encoded image data
        
    Returns:
        The analysis text from Ollama or None if failed
    """
    prompt = """Analyze the provided image and suggest the following in a structured format:
1. A concise, descriptive filename suggestion (lowercase, use underscores instead of spaces, keep it relatively short, suitable for a file system, EXCLUDE the file extension).
2. A brief description sentence for the image (max 1-2 sentences).
3. A comma-separated list of relevant keywords or labels (5-10 labels, lowercase).

Use the following format exactly:
Filename: [your_suggested_filename_base_here]
Description: [Your suggested description here.]
Labels: [label1, label2, label3]
"""

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
        return analysis_text
        
    except Exception as e:
        print(f"\nError communicating with Ollama: {e}", file=sys.stderr)
        print(f"Ensure Ollama is running and the model '{OLLAMA_MODEL}' is available.", file=sys.stderr)
        return None

def parse_ollama_response(analysis_text: str) -> Tuple[str, str, List[str]]:
    """
    Parse the response from Ollama into components.
    
    Args:
        analysis_text: The raw text response from Ollama
        
    Returns:
        Tuple of (filename_base, description, labels_list)
    """
    suggested_filename_base_raw = "unknown_image"
    suggested_description = "No description generated."
    suggested_labels_str = ""
    labels_list = []

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

        # Clean up labels - ensure we never return None for labels
        if suggested_labels_str:
            labels_list = [label.strip().lower() for label in suggested_labels_str.split(',') if label.strip()]
        else:
            labels_list = ["no_labels_generated"]

        return suggested_filename_base_raw, suggested_description, labels_list

    except Exception as e:
        print(f"\nError parsing Ollama response: {e}", file=sys.stderr)
        print("The model might not have followed the expected format.")
        print(f"--- Raw Ollama Response ---\n{analysis_text}\n--------------------------")
        return "analysis_failed", "Failed to parse description.", ["parsing_error"]

def analyze_image_with_ollama(image_path: str) -> Tuple[Optional[str], Optional[str], List[str], Optional[str]]:
    """
    Analyzes an image using Ollama and the specified model.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (suggested_filename_base, suggested_description, suggested_labels_list, image_format)
             or (None, None, [], None) on failure.
    """
    print(f"Analysing '{os.path.basename(image_path)}'...")
    
    # Prepare the image data
    base64_image, image_format = prepare_image_data(image_path)
    if base64_image is None:
        return None, None, [], None
    
    # Call the Ollama API
    analysis_text = call_ollama_api(base64_image)
    if analysis_text is None:
        return None, None, [], image_format
    
    # Parse the response
    filename_base, description, labels = parse_ollama_response(analysis_text)
    return filename_base, description, labels, image_format

def check_exiftool_available() -> bool:
    """
    Check if exiftool is available in the path.
    
    Returns:
        True if exiftool is available, False otherwise
    """
    exiftool_path = shutil.which("exiftool")
    if not exiftool_path:
        print("Error: 'exiftool' command not found. Cannot write metadata or rename.", file=sys.stderr)
        return False
    return True

def write_metadata(file_path: str, description: Optional[str], labels: List[str]) -> bool:
    """
    Write metadata to an image file using exiftool.
    
    Args:
        file_path: Path to the image file
        description: Description to write
        labels: List of labels/keywords to write
        
    Returns:
        True if successful, False otherwise
    """
    if not check_exiftool_available():
        return False
        
    cmd = [shutil.which("exiftool"), "-overwrite_original", "-q"] # -q for quieter operation
    tags_to_write = []
    
    if description and description not in ("No description generated.", "Failed to parse description."):
        tags_to_write.append(f"-XMP-dc:Description={description}")
        tags_to_write.append(f"-IPTC:Caption-Abstract={description}")

    if labels and labels != ["parsing_error"] and labels != ["no_labels_generated"]:
        # Clear existing subjects/keywords
        tags_to_write.append("-Subject=")
        for label in labels:
            tags_to_write.append(f"-Subject={label}")

    if not tags_to_write:
        print("No valid metadata suggestions to write.")
        return True  # No data to write counts as 'success'
        
    cmd.extend(tags_to_write)
    cmd.append(file_path)

    print(f"Running exiftool to write metadata to '{os.path.basename(file_path)}'...")
    try:
        # Add proper charset handling for non-english characters
        env = os.environ.copy()
        env['EXIFTOOL_CHARSET'] = 'UTF8'
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, 
                              encoding='utf-8', errors='replace', env=env)
        print("Exiftool metadata write successful.")
        if result.stderr.strip():
            print(f"Exiftool warnings:\n{result.stderr.strip()}", file=sys.stderr)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error running exiftool: {e}", file=sys.stderr)
        print(f"Command: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"Return Code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(f"Output:\n{e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"Error Output:\n{e.stderr}", file=sys.stderr)
        return False
        
    except Exception as e:
        print(f"An unexpected error occurred while running exiftool: {e}", file=sys.stderr)
        return False

def rename_file(original_path: str, new_filename_base: str, force: bool = False) -> Tuple[bool, str]:
    """
    Rename a file with the suggested filename.
    
    Args:
        original_path: Path to the original file
        new_filename_base: Base name for the new filename (without extension)
        force: Whether to force overwrite existing files
        
    Returns:
        Tuple of (success, new_path)
    """
    abs_original_path = os.path.abspath(original_path)
    original_dir = os.path.dirname(abs_original_path)
    original_basename = os.path.basename(abs_original_path)
    _, original_ext = os.path.splitext(original_basename)

    # Sanitize and create the full new filename
    new_full_filename = sanitize_filename(new_filename_base, original_ext)
    new_path = os.path.join(original_dir, new_full_filename)

    # If the original and new paths are the same, skip renaming
    if abs_original_path == new_path:
        print(f"Suggested filename '{new_full_filename}' is the same as the original. Skipping rename.")
        return True, abs_original_path

    print(f"Attempting rename: '{original_basename}' -> '{new_full_filename}'")
    
    try:
        # Check if target file exists
        if os.path.exists(new_path):
            if force:
                 print(f"Warning: Target file '{new_path}' already exists. Forcing rename (will overwrite!).")
                 os.remove(new_path)
                 print(f"Removed existing file: '{new_path}'")
            else:
                print(f"Error: Target filename '{new_path}' already exists. Rename aborted.", file=sys.stderr)
                print("Use --force to overwrite.")
                return False, abs_original_path

        os.rename(abs_original_path, new_path)
        print("Rename successful.")
        return True, new_path
        
    except OSError as e:
        print(f"Error renaming file: {e}", file=sys.stderr)
        return False, abs_original_path
        
    except Exception as e:
        print(f"An unexpected error occurred during rename: {e}", file=sys.stderr)
        return False, abs_original_path

def write_metadata_and_rename(original_path: str, new_filename_base: str, 
                            description: Optional[str], labels: List[str], 
                            image_format: Optional[str], force: bool = False) -> Tuple[bool, str]:
    """
    Writes metadata using exiftool and renames the file.
    
    Args:
        original_path: Path to the original image file
        new_filename_base: The suggested new filename base (without extension)
        description: The description to write
        labels: A list of labels (keywords) to write
        image_format: The detected image format (used for warning)
        force: Whether to force overwrite existing files
        
    Returns:
        Tuple of (success, new_path)
    """
    print("\n--- Applying Changes ---")
    
    # Write metadata
    metadata_success = write_metadata(original_path, description, labels)
    
    # Rename the file
    rename_success, new_path = rename_file(original_path, new_filename_base, force)
    
    # Operation is successful only if both steps succeeded
    return metadata_success and rename_success, new_path

def process_single_file(file_path: str, write_changes: bool, force_write: bool) -> Tuple[bool, str]:
    """
    Analyzes and optionally modifies a single image file.
    
    Args:
        file_path: Path to the image file
        write_changes: Whether to write changes to the file
        force_write: Whether to force changes without confirmation
        
    Returns:
        Tuple of (success, final_path)
    """
    print(f"\n--- Processing File: {file_path} ---")
    final_path = file_path

    # 1. Analyze the image
    filename_base, description, labels, img_format = analyze_image_with_ollama(file_path)

    if filename_base is None:
        print(f"Analysis failed for {file_path}. Skipping further actions.")
        return False, final_path

    # Get original extension to build the full suggested filename
    _, original_ext = os.path.splitext(file_path)
    suggested_full_filename = sanitize_filename(filename_base, original_ext)

    # 2. Print Suggestions
    print("\n--- Suggestions ---")
    print(f"Suggested Filename : {suggested_full_filename}")
    print(f"Suggested Desc.    : {description}")
    # Ensure labels is never None before joining
    label_str = ', '.join(labels) if labels else "None"  # Using if-else to handle potential None
    print(f"Suggested Labels   : {label_str}")
    print(f"Detected Format    : {img_format or 'Unknown'}")

    # 3. Write changes if requested
    if write_changes:
        write_success, final_path = write_metadata_and_rename(
            file_path,
            filename_base,
            description,
            labels,
            img_format,
            force=force_write
        )
        success = write_success
    else:
        print("\nRun with -w (prompt) or -f (force) to apply these changes (requires exiftool).")
        success = True  # Analysis succeeded, no write requested

    print(f"--- Finished Processing: {os.path.basename(final_path)} ---")
    return success, final_path

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
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
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Automatically answer 'yes' to all prompts. Useful for scripting."
    )
    return parser.parse_args()

def get_files_to_process(input_path: str) -> Tuple[List[str], bool, int]:
    """
    Get list of files to process based on input path.
    
    Args:
        input_path: Path to file or directory
        
    Returns:
        Tuple of (files_list, is_directory, error_code)
        error_code is 0 for success, 1 for error
    """
    abs_input_path = os.path.abspath(input_path)
    files_to_process = []
    is_dir = False
    
    # Handle single file case
    if os.path.isfile(abs_input_path):
        _, ext = os.path.splitext(abs_input_path)
        if ext.lstrip('.').lower() in METADATA_SUPPORTING_FORMATS_LOWER:
            files_to_process.append(abs_input_path)
        else:
            print(f"Error: Input file '{abs_input_path}' does not have a supported extension.", file=sys.stderr)
            print(f"Supported formats: {', '.join(sorted(METADATA_SUPPORTING_FORMATS_LOWER))}")
            return [], False, 1
    
    # Handle directory case
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
            return [], True, 0
    
    # Handle invalid path
    else:
        print(f"Error: Input path '{abs_input_path}' is not a valid file or directory.", file=sys.stderr)
        return [], False, 1
        
    return files_to_process, is_dir, 0

def confirm_write_operation(files: List[str], is_dir: bool, input_path: str, force: bool) -> Tuple[bool, bool]:
    """
    Confirm write operation with the user.
    
    Args:
        files: List of files to process
        is_dir: Whether the input is a directory
        input_path: The input path
        force: Whether to force write without confirmation
        
    Returns:
        Tuple of (should_write, proceed_with_write)
    """
    should_write = force or len(files) > 0
    proceed_with_write = force
    
    if should_write and not force:
        print(f"\n*** WARNING: You requested to write changes! ***")
        if is_dir:
            print(f"This will attempt to modify {len(files)} file(s) in '{input_path}'.")
        else:
            print(f"  - Metadata will be written to: '{os.path.basename(files[0])}'")
            print(f"  - File may be RENAMED based on analysis.")
            
        print(f"  - Existing files with the new name will cause an error unless --force is used.")
        
        try:
            # Check if running in an interactive environment
            if sys.stdin.isatty():
                confirm = input("Proceed with writing changes? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    proceed_with_write = True
                else:
                    print("Write operation cancelled by user.")
                    should_write = False
            else:
                # Non-interactive mode - don't proceed with writing
                print("Not running in interactive terminal. Use --force to write changes.")
                should_write = False
        except (EOFError, KeyboardInterrupt):
            print("\nInput interrupted. Operation cancelled.")
            should_write = False
            
    elif force:
        print(f"\n*** WARNING: --force specified! Applying changes WITHOUT confirmation! ***")
        print(f"***          Existing target files during rename WILL BE OVERWRITTEN! ***")
        
    return should_write, proceed_with_write

def main() -> int:
    """
    Main program execution.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()
    setup_logging()
    
    # Get files to process
    files_to_process, is_dir, error_code = get_files_to_process(args.input_path)
    if error_code != 0:
        return error_code
    
    # Exit if no files to process
    if not files_to_process:
        print("No files to process.")
        return 0
        
    # If --yes option is provided, treat it like force but just for confirmation
    force_confirmation = args.force or args.yes
    
    # Determine if writing should happen and get confirmation
    should_write, proceed_with_write = confirm_write_operation(
        files_to_process, is_dir, args.input_path, force_confirmation)

    # Process the files
    total_files = len(files_to_process)
    success_count = 0
    fail_count = 0
    
    # Break the complex function into smaller parts by using
    # separate processing for batch and single files
    if total_files == 0:
        print("No files to process.")
        return 0

    for i, file_path in enumerate(files_to_process):
        if is_dir:
            print(f"\n{'='*10} Processing file {i+1} of {total_files} {'='*10}")

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

    return 1 if fail_count > 0 else 0

if __name__ == "__main__":
    sys.exit(main())