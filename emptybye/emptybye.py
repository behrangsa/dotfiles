#!/usr/bin/env python3

"""
EmptyBye - A utility to find and remove empty directories.

This script performs a depth-first search on a given directory to identify and remove
empty directories. A directory is considered empty if it contains no files and no
non-empty subdirectories.
"""

import os
import sys
import argparse
from typing import List
import logging

def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def is_directory_empty(path: str) -> bool:
    """
    Check if a directory is empty.
    
    Args:
        path: Path to the directory to check
        
    Returns:
        bool: True if directory is empty, False otherwise
        
    Note: Hidden files are also considered when checking if a directory is empty.
    """
    try:
        with os.scandir(path) as it:
            return not any(True for _ in it)
    except PermissionError:
        logging.error(f"Permission denied: Cannot access {path}")
        return False
    except OSError as e:
        logging.error(f"Error checking directory {path}: {e}")
        return False

def find_empty_dirs(root_path: str) -> List[str]:
    """
    Perform depth-first search to find all empty directories.
    
    Args:
        root_path: The root directory to start the search from
        
    Returns:
        List[str]: List of paths to empty directories, sorted by depth (deepest first)
    """
    empty_dirs = []
    
    try:
        # First pass: collect initially empty directories
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
            if dirpath != root_path and is_directory_empty(dirpath):
                empty_dirs.append(dirpath)
    except PermissionError as e:
        logging.error(f"Permission denied while traversing {root_path}: {e}")
    except OSError as e:
        logging.error(f"Error while traversing directory structure: {e}")
        
    return sorted(empty_dirs, key=len, reverse=True)  # Sort by path length to process deepest dirs first

def remove_empty_dirs(empty_dirs: List[str], dry_run: bool = False) -> None:
    """
    Remove the empty directories from the filesystem.
    
    Args:
        empty_dirs: List of empty directory paths to remove
        dry_run: If True, only print what would be done without actually removing
    """
    removed = set()
    
    while empty_dirs:
        current_empty_dirs = empty_dirs[:]
        empty_dirs.clear()
        
        for dir_path in current_empty_dirs:
            try:
                if is_directory_empty(dir_path):  # Recheck emptiness before removing
                    if dry_run:
                        logging.info(f"Would remove: {dir_path}")
                    else:
                        os.rmdir(dir_path)
                        logging.info(f"Removed: {dir_path}")
                    removed.add(dir_path)
                    
                    # Check if parent is now empty
                    parent = os.path.dirname(dir_path)
                    if parent and parent != os.path.dirname(parent):  # Skip root directory
                        if is_directory_empty(parent) and parent not in removed:
                            empty_dirs.append(parent)
                            
            except PermissionError:
                logging.error(f"Permission denied: Cannot remove {dir_path}")
            except OSError as e:
                logging.error(f"Error removing directory {dir_path}: {e}")

def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Find and remove empty directories using depth-first search."
    )
    parser.add_argument(
        "directory",
        help="The root directory to search for empty directories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing anything"
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        logging.error(f"Error: {args.directory} is not a directory")
        sys.exit(1)
        
    setup_logging()
    
    logging.info(f"Scanning directory: {args.directory}")
    empty_dirs = find_empty_dirs(args.directory)
    
    if not empty_dirs:
        logging.info("No empty directories found.")
        return
        
    logging.info(f"Found {len(empty_dirs)} empty directories")
    remove_empty_dirs(empty_dirs, args.dry_run)

if __name__ == "__main__":
    main()