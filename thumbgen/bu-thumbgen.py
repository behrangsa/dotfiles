#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Script to generate thumbnails for given files using GnomeDesktop.ThumbnailFactory.
# Intended to be called by incron or manually when a file is created/modified.
# Example incron usage in user's incrontab (incrontab -e):
# /path/to/your/pictures IN_CLOSE_WRITE,IN_CREATE /usr/local/bin/generate_gnome_thumbnail.py $@/$#
# (Make sure this script is executable: chmod +x /usr/local/bin/generate_gnome_thumbnail.py)

import gi
import os
import sys
import argparse
import logging
import logging.handlers # For SysLogHandler

# --- PyGObject Namespace Versioning ---
# Attempt to require GnomeDesktop version.
# The PyGIWarning typically suggests '4.0' for modern GNOME systems (GTK4 based).
# If this fails, the script cannot proceed.
try:
    gi.require_version('GnomeDesktop', '4.0')
except ValueError as e:
    # This error message is critical for troubleshooting if dependencies are missing.
    sys.stderr.write(f"CRITICAL ERROR: Failed to require GnomeDesktop version: {e}\n")
    sys.stderr.write(
        "Please ensure the correct libgnome-desktop library and its GObject Introspection "
        "data are installed correctly for the '4.0' API.\n"
        "For Debian/Ubuntu, this might be 'libgnome-desktop-4-dev' (which provides the library) "
        "and 'gir1.2-gnomedesktop-4.0' (for introspection).\n"
    )
    sys.exit(1) # Exit immediately if core dependency isn't met.

from gi.repository import Gio, GnomeDesktop, GLib

# --- Script Configuration ---
SCRIPT_BASENAME = os.path.basename(__file__)
LOGGER_NAME = "gnome_thumbnail_generator" # Logger name
LOG_LEVEL = logging.INFO # Default log level (INFO, DEBUG, WARNING, ERROR)

# For production incron usage, set USE_SYSLOG to True.
# This will send log messages to the system logger.
# Ensure the user running the incron job has permissions to write to /dev/log.
USE_SYSLOG = False # CHANGE TO True FOR PRODUCTION INCRON JOBS

# Define which thumbnail sizes to attempt to generate.
# GnomeDesktop.ThumbnailSize.LARGE is typically 256x256.
# GnomeDesktop.ThumbnailSize.NORMAL is typically 128x128.
THUMBNAIL_SIZES_TO_GENERATE = [
    GnomeDesktop.ThumbnailSize.NORMAL,
    GnomeDesktop.ThumbnailSize.LARGE
]

# --- Logger Setup ---
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(LOG_LEVEL)
# Prevent log duplication if an incron daemon already captures stdout/stderr
logger.propagate = False 

# Remove existing handlers to prevent duplication if script is re-run in same process (unlikely for incron)
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

if USE_SYSLOG and not '--force-console-log' in sys.argv: # Check for override later
    # SysLogHandler for Linux. Address might be '/var/run/syslog' on some systems.
    syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
    # Example syslog format: gnome_thumbnail_generator: INFO Message content
    syslog_formatter = logging.Formatter(f'{SCRIPT_BASENAME}: %(levelname)s %(message)s')
    syslog_handler.setFormatter(syslog_formatter)
    logger.addHandler(syslog_handler)
else:
    console_handler = logging.StreamHandler(sys.stdout) # Use sys.stdout or sys.stderr
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def get_thumbnail_size_name(size_enum):
    """Helper function to get a string name for a thumbnail size enum."""
    if size_enum == GnomeDesktop.ThumbnailSize.NORMAL:
        return "NORMAL"
    if size_enum == GnomeDesktop.ThumbnailSize.LARGE:
        return "LARGE"
    return "UNKNOWN_SIZE"


def create_thumbnail_for_size(filepath, thumbnail_size_enum):
    """
    Attempts to create a thumbnail for the given filepath and specific size.

    Args:
        filepath (str): The absolute, canonical path to the file.
        thumbnail_size_enum (GnomeDesktop.ThumbnailSize): The desired thumbnail size enum.

    Returns:
        bool: True if a thumbnail was successfully generated, if a fresh one already existed,
              or if the system determined it cannot/should not thumbnail this file (not an error).
              False if an actual error occurred during an attempted generation.
    """
    size_name = get_thumbnail_size_name(thumbnail_size_enum)
    logger.debug(f"Processing file '{filepath}' for {size_name} thumbnail.")

    try:
        gfile = Gio.File.new_for_path(filepath)
        # It's crucial to use the canonical URI for cache lookups and consistency.
        # The factory methods usually work with GFile objects directly.
        uri_for_logging = gfile.get_uri()

        # File modification time (mtime) in seconds since Epoch.
        # os.path.getmtime() returns float; factory might expect int or handle float.
        # Let's provide it as an integer number of seconds.
        file_mtime = int(os.path.getmtime(filepath))

        file_info = gfile.query_info(
            Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE, # Standard way to get MIME type
            Gio.FileQueryInfoFlags.NONE,
            None # Cancellable
        )
        mimetype = file_info.get_content_type()

        if not mimetype:
            logger.warning(f"Could not determine MIME type for '{uri_for_logging}'. Skipping {size_name} thumbnail.")
            return True # Not an error of this script, but a file characteristic.

        logger.debug(f"File '{uri_for_logging}': MIME '{mimetype}', mtime {file_mtime}, TargetSize {size_name}.")

        factory = GnomeDesktop.ThumbnailFactory.new(thumbnail_size_enum)

        # Check if thumbnailing is possible and if a thumbnail is needed (e.g., not already fresh).
        # can_thumbnail considers if a valid thumbnailer is registered and if a current thumbnail exists.
        if factory.can_thumbnail(gfile, mimetype, file_mtime):
            logger.info(f"Attempting to generate {size_name} thumbnail for '{uri_for_logging}' (MIME: {mimetype}).")
            
            # This is a blocking call.
            thumbnail_path = factory.generate_thumbnail(gfile, mimetype)

            if thumbnail_path:
                logger.info(f"Successfully generated {size_name} thumbnail for '{uri_for_logging}' at '{thumbnail_path}'.")
                return True
            else:
                # This indicates a failure within the thumbnailer for this specific file/mimetype,
                # even though can_thumbnail reported it was possible.
                logger.error(
                    f"Thumbnail generation FAILED for '{uri_for_logging}' (MIME: {mimetype}, Size: {size_name}) "
                    "by the factory, despite can_thumbnail returning true. The specific thumbnailer might have failed."
                )
                return False # Explicit failure
        else:
            # If can_thumbnail is false, check if it's because a fresh one already exists.
            existing_thumb_path = factory.lookup(gfile, file_mtime) # mtime helps check freshness
            if existing_thumb_path:
                logger.debug(f"Fresh {size_name} thumbnail already exists for '{uri_for_logging}' at '{existing_thumb_path}'. No action needed.")
                return True
            else:
                logger.info(
                    f"Cannot or not necessary to generate {size_name} thumbnail for '{uri_for_logging}' "
                    f"(MIME: {mimetype}). No suitable thumbnailer registered, file type unsupported by "
                    "GNOME's current thumbnailers, or it's a type that isn't typically thumbnailed."
                )
                return True # Not an error of this script, but a system/config state.

    except GLib.Error as e:
        # GLib.Error can be raised for various GIO issues (e.g., file access problems not caught by initial checks).
        logger.error(f"GLib/Gio error while processing '{filepath}' for {size_name} thumbnail: {e.message} (code: {e.code})")
        return False
    except FileNotFoundError:
        # This should ideally be caught by the initial checks in main(),
        # but including for robustness if create_thumbnail_for_size is called directly.
        logger.error(f"File not found during {size_name} thumbnail processing: '{filepath}'")
        return False
    except Exception as e:
        # Catch any other unexpected exceptions.
        logger.exception(f"An unexpected error occurred creating {size_name} thumbnail for '{filepath}': {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generates thumbnails for a given file using GNOME Desktop services. "
                    "Suitable for use with incron or similar file monitoring tools.",
        epilog=f"Example: {SCRIPT_BASENAME} /path/to/your/file.jpg"
    )
    parser.add_argument(
        "filepath",
        type=str,
        help="The path to the file for which to generate thumbnails."
    )
    parser.add_argument(
        "--force-console-log",
        action="store_true",
        help="Force logging to console, overriding USE_SYSLOG in the script (for debugging)."
    )
    args = parser.parse_args()

    # Handle --force-console-log if USE_SYSLOG was initially True
    if args.force_console_log and USE_SYSLOG:
        logger.info("Syslog was configured, but --force-console-log overrides it.")
        for h in logger.handlers[:]: # Make a copy for iteration
            if isinstance(h, logging.handlers.SysLogHandler):
                logger.removeHandler(h)
        
        # Add console handler if it wasn't already the default
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        logger.info("Logging forced to console.")


    # --- File Path Validation and Canonicalization ---
    try:
        # Expand user tilde (~) if present.
        expanded_filepath = os.path.expanduser(args.filepath)
        # Get absolute path to handle relative paths.
        # os.path.realpath also resolves any symbolic links, crucial for a canonical URI.
        canonical_filepath = os.path.realpath(expanded_filepath)
    except Exception as e:
        logger.error(f"Could not resolve input path '{args.filepath}' to a canonical path: {e}")
        sys.exit(1)

    logger.debug(f"Resolved input '{args.filepath}' to canonical path '{canonical_filepath}'.")

    if not os.path.exists(canonical_filepath):
        logger.error(f"Input file does not exist: '{canonical_filepath}'")
        sys.exit(1)

    if not os.path.isfile(canonical_filepath):
        logger.error(f"Input path is not a file: '{canonical_filepath}'")
        sys.exit(1)

    if not os.access(canonical_filepath, os.R_OK):
        logger.error(f"Input file is not readable (permission denied): '{canonical_filepath}'")
        sys.exit(1)
    
    logger.info(f"Request to generate thumbnails for: '{canonical_filepath}'")

    # --- Process Thumbnails ---
    overall_success = True
    for size_enum in THUMBNAIL_SIZES_TO_GENERATE:
        # If any size explicitly fails (returns False from create_thumbnail_for_size),
        # the overall operation is marked as not entirely successful.
        if not create_thumbnail_for_size(canonical_filepath, size_enum):
            overall_success = False
    
    if overall_success:
        logger.info(
            f"All requested thumbnail operations for '{canonical_filepath}' completed. "
            "This may include finding existing fresh thumbnails or determining that some sizes were unsupported/not needed."
        )
        sys.exit(0)
    else:
        # This means at least one thumbnail size that was attempted resulted in an explicit failure.
        logger.error(
            f"One or more thumbnail sizes encountered an error during generation for '{canonical_filepath}'. "
            "Review logs for details."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

