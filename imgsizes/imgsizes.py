#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generates multiple resized variations of images using ImageMagick.

This script takes a path to an image file or a directory containing images
and creates resized versions (32x32, 64x64, 128x128, 256x256, 512x512)
using the ImageMagick 'convert' command with the Catmull-Rom filter.
"""

import argparse
import logging
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Set

# --- Configuration ---

# Target sizes for the resized images
TARGET_SIZES: List[int] = [32, 64, 128, 256, 512]

# ImageMagick filter to use for resizing
RESIZE_FILTER: str = "Catrom"

# Common image file extensions (case-insensitive)
IMAGE_EXTENSIONS: Set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
}

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# --- Core Functions ---

def check_imagemagick() -> None:
    """
    Checks if the ImageMagick 'convert' command is available in the PATH.
    Exits the script if not found.
    """
    if shutil.which("convert") is None:
        log.error("Error: ImageMagick 'convert' command not found in PATH.")
        log.error(
            "Please install ImageMagick. (e.g., 'sudo apt install imagemagick' "
            "or 'brew install imagemagick')"
        )
        sys.exit(1)
    log.debug("ImageMagick 'convert' command found.")


def generate_resized_image(
    input_path: Path, output_path: Path, size: int, filter_name: str
) -> bool:
    """
    Uses the ImageMagick 'convert' command to resize a single image.

    Args:
        input_path: Path to the source image file.
        output_path: Path where the resized image will be saved.
        size: The target size (width and height).
        filter_name: The ImageMagick filter to use for resizing.

    Returns:
        True if the conversion was successful, False otherwise.

    Raises:
        FileNotFoundError: If the input_path does not exist.
        PermissionError: If there are permission issues reading/writing files.
        Exception: For other potential errors during subprocess execution.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input image not found: {input_path}")

    # Construct the ImageMagick command
    # Using list format is safer, prevents shell injection issues
    command = [
        "convert",
        str(input_path),
        "-filter",
        filter_name,
        "-resize",
        f"{size}x{size}",  # Resize to square dimensions
        str(output_path),
    ]

    log.info(
        f"Generating {size}x{size} version for '{input_path.name}' -> '{output_path.name}'"
    )
    log.debug(f"Executing command: {' '.join(shlex.quote(str(arg)) for arg in command)}")

    try:
        # Execute the command
        process = subprocess.run(
            command,
            check=True,  # Raise CalledProcessError on non-zero exit code
            capture_output=True,  # Capture stdout and stderr
            text=True,  # Decode output as text
            encoding='utf-8'
        )
        log.debug(f"ImageMagick stdout:\n{process.stdout}")
        if process.stderr:
            # ImageMagick often prints warnings to stderr, log them
            log.warning(f"ImageMagick stderr:\n{process.stderr}")
        log.info(f"Successfully created: {output_path}")
        return True

    except FileNotFoundError:
        # This should theoretically be caught by check_imagemagick,
        # but handle defensively.
        log.error(
             "Error: 'convert' command not found during execution. "
             "Is ImageMagick installed and in PATH?"
        )
        return False
    except subprocess.CalledProcessError as e:
        log.error(f"ImageMagick failed for {input_path} -> {output_path}")
        log.error(f"Command: {' '.join(shlex.quote(str(arg)) for arg in e.cmd)}")
        log.error(f"Return Code: {e.returncode}")
        log.error(f"Stderr:\n{e.stderr}")
        # Attempt to remove potentially corrupted/incomplete output file
        if output_path.exists():
            try:
                output_path.unlink()
                log.warning(f"Removed potentially incomplete file: {output_path}")
            except OSError as rm_err:
                log.error(f"Failed to remove incomplete file {output_path}: {rm_err}")
        return False
    except PermissionError as e:
        log.error(f"Permission error processing {input_path} or writing to {output_path}: {e}")
        raise  # Re-raise permission errors as they might indicate a setup issue
    except Exception as e:
        log.error(f"An unexpected error occurred during conversion: {e}")
        # Attempt to remove potentially corrupted/incomplete output file
        if output_path.exists():
            try:
                output_path.unlink()
                log.warning(f"Removed potentially incomplete file: {output_path}")
            except OSError as rm_err:
                log.error(f"Failed to remove incomplete file {output_path}: {rm_err}")
        raise # Re-raise unexpected errors


def process_image_file(image_path: Path) -> int:
    """
    Generates resized variations for a single image file.

    Args:
        image_path: Path to the image file to process.

    Returns:
        The number of successfully generated variations.

    Edge Cases Handled:
        - Input path is not a file.
        - Input file is not a recognized image type.
        - Output directory is not writable (caught by generate_resized_image).
        - ImageMagick conversion errors (logged by generate_resized_image).
    """
    if not image_path.is_file():
        log.warning(f"Skipping non-file path: {image_path}")
        return 0

    # Check if the file extension is a known image type
    if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
        log.warning(
            f"Skipping file with unrecognized extension "
            f"'{image_path.suffix}': {image_path.name}"
        )
        return 0

    log.info(f"Processing image file: {image_path}")
    output_dir = image_path.parent
    base_name = image_path.stem
    extension = image_path.suffix
    success_count = 0

    for size in TARGET_SIZES:
        # Construct the output filename, e.g., image_128x128.png
        output_filename = f"{base_name}_{size}x{size}{extension}"
        output_path = output_dir / output_filename

        # Avoid overwriting the source if its name matches the pattern
        if image_path == output_path:
             log.warning(
                 f"Skipping size {size} for {image_path.name} because "
                 f"output name matches input name."
             )
             continue

        try:
            if generate_resized_image(image_path, output_path, size, RESIZE_FILTER):
                success_count += 1
        except (FileNotFoundError, PermissionError) as e:
            # Log errors already handled within generate_resized_image
            # or raised if fundamental issues exist.
            log.error(f"Failed to process {image_path} for size {size}: {e}")
            # Stop processing this file if critical error occurred
            if isinstance(e, PermissionError):
                 log.error("Stopping processing due to permission error.")
                 break # Stop trying other sizes for this file
        except Exception as e:
            log.error(f"Unexpected error processing {image_path} for size {size}: {e}")
            # Decide whether to continue with other sizes or stop
            # For now, log and continue with next size.
            pass


    return success_count


def process_directory(dir_path: Path) -> int:
    """
    Finds image files in a directory and processes each one.

    Args:
        dir_path: Path to the directory to scan for images.

    Returns:
        The total number of successfully generated variations across all images.

    Edge Cases Handled:
        - Input path is not a directory.
        - Directory is not readable.
        - Directory contains subdirectories (they are ignored).
        - Directory contains non-image files (they are ignored).
    """
    if not dir_path.is_dir():
        log.error(f"Error: Input path is not a directory: {dir_path}")
        return 0

    log.info(f"Processing directory: {dir_path}")
    total_success_count = 0
    processed_files = 0

    try:
        for item_path in dir_path.iterdir():
            if item_path.is_file():
                # Check extension before calling process_image_file
                if item_path.suffix.lower() in IMAGE_EXTENSIONS:
                    processed_files += 1
                    total_success_count += process_image_file(item_path)
                else:
                     log.debug(f"Skipping non-image file: {item_path.name}")
            elif item_path.is_dir():
                log.debug(f"Skipping subdirectory: {item_path.name}")
            # Add handling for other file types like symlinks if necessary
            # else:
            #    log.debug(f"Skipping non-file/non-directory item: {item_path.name}")

    except PermissionError as e:
        log.error(f"Permission error reading directory {dir_path}: {e}")
        return total_success_count # Return count so far
    except Exception as e:
        log.error(f"An unexpected error occurred while iterating directory {dir_path}: {e}")
        return total_success_count # Return count so far

    log.info(f"Finished processing directory '{dir_path}'. Processed {processed_files} image files.")
    return total_success_count

# --- Main Execution ---

def main():
    """
    Parses command-line arguments and orchestrates the image processing.
    """
    parser = argparse.ArgumentParser(
        description="Generate resized variations of images using ImageMagick.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Process a single image file
  python %(prog)s /path/to/my_image.png

  # Process all images in a directory
  python %(prog)s /path/to/image_directory/
"""
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to the input image file or directory containing images.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging."
    )

    args = parser.parse_args()

    # Adjust log level if verbose flag is set
    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug("Verbose logging enabled.")

    # --- Prerequisites Check ---
    check_imagemagick()

    # --- Input Path Validation and Processing ---
    input_path: Path = args.input_path

    try:
        if not input_path.exists():
            log.error(f"Error: Input path does not exist: {input_path}")
            sys.exit(1)

        total_generated = 0
        if input_path.is_file():
            total_generated = process_image_file(input_path)
        elif input_path.is_dir():
            total_generated = process_directory(input_path)
        else:
            log.error(f"Error: Input path is neither a file nor a directory: {input_path}")
            sys.exit(1)

        log.info(f"Processing complete. Total variations generated: {total_generated}")

    except FileNotFoundError:
         # Should be caught earlier, but handle defensively
        log.error(f"Error: Input path not found: {input_path}")
        sys.exit(1)
    except PermissionError as e:
        log.error(f"A permission error occurred: {e}")
        log.error("Please check read/write permissions for the input path and its contents.")
        sys.exit(1)
    except Exception as e:
        log.exception(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

