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
from typing import List, Set, Tuple
import logging
import time

def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: If True, set log level to DEBUG; otherwise INFO
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def is_directory_empty(path: str, follow_symlinks: bool = False) -> bool:
    """
    Check if a directory is empty.
    
    Args:
        path: Path to the directory to check
        follow_symlinks: Whether to follow symbolic links to directories
        
    Returns:
        bool: True if directory is empty, False otherwise
        
    Note: Hidden files are also considered when checking if a directory is empty.
    """
    try:
        with os.scandir(path) as it:
            for entry in it:
                # If follow_symlinks is False, treat symlinks as content
                # If follow_symlinks is True, only count non-symlink entries or symlinks that point to content
                if not follow_symlinks or not entry.is_symlink():
                    return False
                # If following symlinks and entry is a symlink to an empty dir, continue checking
                elif entry.is_dir(follow_symlinks=True):
                    if not is_directory_empty(entry.path, follow_symlinks):
                        return False
            return True
    except PermissionError:
        logging.error(f"Permission denied: Cannot access {path}")
        return False
    except OSError as e:
        logging.error(f"Error checking directory {path}: {e}")
        return False

def get_directory_depth(path: str) -> int:
    """
    Calculate the depth of a directory path by counting path separators.
    
    Args:
        path: The directory path
        
    Returns:
        int: The depth of the directory
    """
    # Normalize path to handle different formats
    norm_path = os.path.normpath(path)
    return norm_path.count(os.sep)

def find_empty_dirs(root_path: str, follow_symlinks: bool = False) -> List[str]:
    """
    Perform depth-first search to find all empty directories.
    
    Args:
        root_path: The root directory to start the search from
        follow_symlinks: Whether to follow symbolic links to directories
        
    Returns:
        List[str]: List of paths to empty directories, sorted by depth (deepest first)
    """
    empty_dirs = []
    root_path = os.path.abspath(root_path)
    
    try:
        # Walk the directory tree bottom-up
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=False, followlinks=follow_symlinks):
            # Skip the root directory during collection (it will be evaluated later if needed)
            if dirpath != root_path and is_directory_empty(dirpath, follow_symlinks):
                empty_dirs.append(dirpath)
    except PermissionError as e:
        logging.error(f"Permission denied while traversing {root_path}: {e}")
    except OSError as e:
        logging.error(f"Error while traversing directory structure: {e}")
        
    # Sort directories by depth (deepest first) for safe removal
    return sorted(empty_dirs, key=get_directory_depth, reverse=True)

def remove_empty_dirs(empty_dirs: List[str], dry_run: bool = False, 
                     follow_symlinks: bool = False) -> Tuple[int, Set[str]]:
    """
    Remove the empty directories from the filesystem.
    
    Args:
        empty_dirs: List of empty directory paths to remove
        dry_run: If True, only print what would be done without actually removing
        follow_symlinks: Whether to follow symbolic links when determining emptiness
        
    Returns:
        Tuple[int, Set[str]]: Count of removed directories and set of their paths
    """
    removed_count = 0
    removed_dirs = set()
    to_process = set(empty_dirs)  # Use a set to avoid duplicates
    
    # Process list of empty directories
    while to_process:
        # Get a directory to process (convert to list for deterministic order)
        dir_path = sorted(to_process, key=get_directory_depth, reverse=True)[0]
        to_process.remove(dir_path)
        
        # Skip if already processed
        if dir_path in removed_dirs:
            continue
            
        try:
            # Recheck emptiness before removing to avoid race conditions
            if is_directory_empty(dir_path, follow_symlinks):  
                if dry_run:
                    logging.info(f"Would remove: {dir_path}")
                else:
                    os.rmdir(dir_path)
                    logging.info(f"Removed: {dir_path}")
                
                removed_dirs.add(dir_path)
                removed_count += 1
                
                # Add parent to potential_empties if it exists and isn't already processed
                parent = os.path.dirname(dir_path)
                if parent and os.path.isdir(parent) and parent not in removed_dirs:
                    to_process.add(parent)
                    
        except PermissionError:
            logging.error(f"Permission denied: Cannot remove {dir_path}")
        except OSError as e:
            logging.error(f"Error removing directory {dir_path}: {e}")
            
    return removed_count, removed_dirs

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
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links when determining if directories are empty"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set up logging early to capture all messages
    setup_logging(args.verbose)
    
    # Normalize and validate the path
    target_dir = os.path.abspath(args.directory)
    if not os.path.isdir(target_dir):
        logging.error(f"Error: {target_dir} is not a directory")
        sys.exit(1)
        
    start_time = time.time()
    logging.info(f"Scanning directory: {target_dir}")
    
    # Find all initially empty directories
    empty_dirs = find_empty_dirs(target_dir, args.follow_symlinks)
    
    if not empty_dirs:
        logging.info("No empty directories found.")
        return
    
    if args.verbose:
        logging.debug(f"Initially found {len(empty_dirs)} empty directories")
    
    # Remove empty directories and handle chain reactions
    removed_count, removed_dirs = remove_empty_dirs(empty_dirs, args.dry_run, args.follow_symlinks)
    
    # Report results
    action = "Would remove" if args.dry_run else "Removed"
    elapsed_time = time.time() - start_time
    
    if removed_count > 0:
        logging.info(f"{action} {removed_count} empty directories in {elapsed_time:.2f} seconds")
    else:
        logging.info("No directories were removed.")

if __name__ == "__main__":
    main()