#!/usr/bin/env python3
"""
bu-openai.py - Command-line interface for OpenAI API

This script provides a CLI for interacting with OpenAI's API services.
Currently implemented: listing available models.

Author: Behrang Saeedzadeh
License: MIT
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from rich.console import Console
from rich.table import Table
from rich import box

# Constants
API_BASE_URL = "https://api.openai.com/v1"
CONFIG_DIR = Path.home() / ".config" / "openai"
CONFIG_FILE = CONFIG_DIR / "config"
API_KEY_ENV_VAR = "OPENAI_API_KEY"


def get_api_key() -> Optional[str]:
    """
    Retrieve the OpenAI API key from environment variables or config file.
    
    Returns:
        str: The API key if found, None otherwise
    """
    # First check environment variable
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if api_key:
        return api_key
    
    # Then check config file
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if API_KEY_ENV_VAR in line and '=' in line:
                            _, value = line.split('=', 1)
                            # Remove quotes if present
                            api_key = value.strip('" ')
                            if api_key:
                                return api_key
        except Exception as e:
            print(f"Error reading config file: {e}", file=sys.stderr)
    
    return None


def configure_api_key() -> None:
    """
    Interactively configure and save the OpenAI API key.
    """
    print("OpenAI API Key Configuration")
    print("--------------------------")
    
    api_key = input("Enter your OpenAI API key: ").strip()
    if not api_key:
        print("Error: API key cannot be empty", file=sys.stderr)
        sys.exit(1)
    
    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set secure permissions on config directory
    os.chmod(CONFIG_DIR, 0o700)
    
    # Get current date for the config file header
    current_date = os.popen('date').read().strip()
    
    # Write config file
    with open(CONFIG_FILE, 'w') as f:
        f.write("# OpenAI API configuration\n")
        f.write(f"# Created: {current_date}\n")
        f.write(f"{API_KEY_ENV_VAR}=\"{api_key}\"\n")
    
    # Set secure permissions on config file
    os.chmod(CONFIG_FILE, 0o600)
    
    print(f"API key saved to {CONFIG_FILE}")


# ---------- Models Command Functions ----------

def fetch_models(api_key: str) -> Dict[str, Any]:
    """
    Fetch available models from the OpenAI API.
    
    Args:
        api_key: OpenAI API key for authentication
        
    Returns:
        Dict containing the API response
        
    Raises:
        requests.RequestException: If the API request fails
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{API_BASE_URL}/models", headers=headers)
    response.raise_for_status()
    return response.json()


def filter_models(models_data: Dict[str, Any], filter_term: Optional[str] = None) -> Dict[str, Any]:
    """
    Filter models based on a search term.
    
    Args:
        models_data: The complete models data from the API
        filter_term: Optional term to filter models by ID
        
    Returns:
        Filtered models data
    """
    if not filter_term:
        return models_data
    
    # Create a new data structure with filtered models
    filtered_data = {"data": [], "object": models_data.get("object", "list")}
    
    for model in models_data.get("data", []):
        model_id = model.get("id", "")
        if filter_term.lower() in model_id.lower():
            filtered_data["data"].append(model)
    
    return filtered_data


def format_model_dates(models_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format Unix timestamps in 'created' fields as date strings (YYYY-MM-DD).
    
    Args:
        models_data: Models data from the API containing Unix timestamps
        
    Returns:
        Updated models data with formatted dates
    """
    import datetime
    
    # Create a deep copy to avoid modifying the original data
    import copy
    formatted_data = copy.deepcopy(models_data)
    
    # Format each 'created' timestamp in the models
    for model in formatted_data.get("data", []):
        if "created" in model and isinstance(model["created"], (int, float)):
            # Convert Unix timestamp to date string (YYYY-MM-DD)
            timestamp = model["created"]
            date_obj = datetime.datetime.fromtimestamp(timestamp)
            date_str = date_obj.strftime("%Y-%m-%d")
            model["created"] = date_str
    
    return formatted_data


def print_models_table(data: Dict[str, Any], format_dates: bool = False, colorize: bool = True) -> None:
    """
    Print models data in a tabular format using the Rich library.
    
    Args:
        data: Models data from the API
        format_dates: Whether to format Unix timestamps as ISO dates
        colorize: Whether to colorize the output
    """
    # Format dates if requested
    if format_dates:
        data = format_model_dates(data)
    
    # Extract models data
    models = data.get("data", [])
    if not models:
        print("No models found.")
        return
    
    # Create console with color setting
    console = Console(no_color=not colorize)
    
    # Create the table
    header_style = "bold cyan" if colorize else "bold"
    table = Table(show_header=True, box=box.SIMPLE, header_style=header_style)
    
    # Add columns with specific widths
    table.add_column("ID", width=30, overflow="ellipsis")
    table.add_column("OWNER", width=15, overflow="ellipsis")
    table.add_column("CREATED", width=10, overflow="ellipsis")  # YYYY-MM-DD format (10 chars)
    table.add_column("PERMISSIONS", overflow="fold")
    
    # Add rows to the table
    for model in models:
        model_id = model.get("id", "")
        owner = model.get("owned_by", "")
        created = str(model.get("created", ""))  # Ensure string type
        
        # Format permissions info
        permissions = "; ".join([p.get("permission_id", "") for p in model.get("permission", [])])
        
        # Add the row to the table
        table.add_row(model_id, owner, created, permissions)
    
    # Print the table
    console.print(table)
    
    # Print total count
    count_style = "bold green" if colorize else ""
    console.print(f"Total models: {len(models)}", style=count_style)


def colorize_json(json_str: str) -> str:
    """
    Apply syntax highlighting to a JSON string.
    
    Args:
        json_str: The JSON string to colorize
        
    Returns:
        Colorized string
    """
    return highlight(json_str, JsonLexer(), TerminalFormatter())


def sort_models_data(data: Dict[str, Any], sort_field: str, descending: bool = False) -> Dict[str, Any]:
    """
    Sort the models data by the specified field.
    
    Args:
        data: Models data from the API
        sort_field: Field to sort by (id, object, created, owned_by)
        descending: Whether to sort in descending order
        
    Returns:
        Sorted models data
    """
    import copy
    sorted_data = copy.deepcopy(data)
    
    # Get the list of models
    models = sorted_data.get("data", [])
    if not models:
        return sorted_data
    
    # Handle special case for created field (it could be a timestamp or a formatted date)
    if sort_field == "created":
        # Try to sort numerically first (for timestamp integers)
        try:
            models.sort(
                key=lambda m: float(m.get(sort_field, 0)) if m.get(sort_field) is not None else 0,
                reverse=descending
            )
        except (ValueError, TypeError):
            # If that fails, sort as strings (for formatted dates)
            models.sort(
                key=lambda m: str(m.get(sort_field, "")) if m.get(sort_field) is not None else "",
                reverse=descending
            )
    else:
        # For other fields, sort as strings
        models.sort(
            key=lambda m: str(m.get(sort_field, "")) if m.get(sort_field) is not None else "",
            reverse=descending
        )
    
    # Update the data with sorted models
    sorted_data["data"] = models
    return sorted_data


def print_models_json(data: Dict[str, Any], pretty: bool = True, format_dates: bool = False, colorize: bool = True) -> None:
    """
    Print models data as JSON to stdout.
    
    Args:
        data: Models data from the API
        pretty: Whether to format the JSON output for readability (default: True)
        format_dates: Whether to format Unix timestamps as ISO dates (default: False)
        colorize: Whether to colorize the output (default: True)
    """
    # Format dates if requested
    if format_dates:
        data = format_model_dates(data)
    
    # Determine if we should use indentation
    indent = 2 if pretty else None
    
    # Convert to JSON string
    json_str = json.dumps(data, indent=indent)
    
    # Apply colorization if requested
    if pretty and colorize:
        result = colorize_json(json_str)
        print(result, end='' if result.endswith('\n') else '\n')
    else:
        # No highlighting
        print(json_str)


def cmd_list_models(args: argparse.Namespace) -> int:
    """
    Implementation for the `ls models` command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Get API key (prioritize command line, then env var, then config file)
    api_key = args.key or get_api_key()
    
    if not api_key:
        print("Error: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable, "
              "provide it with --key, or use 'bu-openai.py configure' to set up.", file=sys.stderr)
        return 1
    
    try:
        # Fetch models from API
        models_data = fetch_models(api_key)
        
        # Filter the data if requested
        if args.filter:
            models_data = filter_models(models_data, args.filter)
        
        # Apply sorting if requested
        if args.sort:
            # Determine sort direction (default is ascending)
            descending = False
            if args.dsc and not args.asc:
                # If --dsc is specified and --asc is not, use descending order
                descending = True
            models_data = sort_models_data(models_data, args.sort, descending)
        
        # Print the results based on format preference
        if args.table:
            # For table format, create Rich console with color setting
            print_models_table(
                models_data,
                format_dates=args.pretty_dates,
                colorize=not args.no_color  # Rich will handle this internally
            )
        else:
            # For JSON format
            print_models_json(
                models_data, 
                pretty=not args.compact, 
                format_dates=args.pretty_dates,
                colorize=not args.no_color
            )
        return 0
        
    except requests.RequestException as e:
        status_code = "unknown"
        error_msg = str(e)
        
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            try:
                error_data = e.response.json()
                if 'error' in error_data and 'message' in error_data['error']:
                    error_msg = error_data['error']['message']
            except ValueError:
                pass  # Keep the original error message if JSON parsing fails
        
        print(f"Error: API request failed (Status code: {status_code})\n{error_msg}", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Error: Failed to parse API response as JSON", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# ---------- Command Routing ----------

def setup_parsers() -> argparse.ArgumentParser:
    """
    Set up the argument parsers for the CLI.
    
    Returns:
        The configured argument parser
    """
    # Main parser
    main_parser = argparse.ArgumentParser(
        description="Command-line interface for OpenAI API"
    )
    
    # Add global arguments
    main_parser.add_argument(
        "-k", "--key",
        help="OpenAI API key (overrides env var and config file)"
    )
    
    # Add version argument
    main_parser.add_argument(
        "-v", "--version",
        action="version",
        version="bu-openai 0.1.0"
    )
    
    # Create subparsers for different commands
    subparsers = main_parser.add_subparsers(dest="command", help="Command to execute")
    
    # Configure command
    subparsers.add_parser("configure", help="Configure API key and settings")
    
    # List command
    list_parser = subparsers.add_parser("ls", help="List resources (models, etc.)")
    list_subparsers = list_parser.add_subparsers(dest="subcommand", help="Resource to list")
    
    # Models subcommand
    models_parser = list_subparsers.add_parser("models", help="List available OpenAI models")
    models_parser.add_argument(
        "-c", "--compact",
        action="store_true",
        help="Output compact JSON without pretty printing"
    )
    models_parser.add_argument(
        "-f", "--filter",
        help="Filter models by name (case-insensitive)"
    )
    models_parser.add_argument(
        "-d", "--pretty-dates",
        action="store_true",
        help="Format 'created' timestamps as dates (YYYY-MM-DD)"
    )
    models_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colorized output"
    )
    models_parser.add_argument(
        "-t", "--table",
        action="store_true",
        help="Display results in a tabular format using Rich"
    )
    models_parser.add_argument(
        "--sort",
        choices=["id", "object", "created", "owned_by"],
        help="Sort results by the specified field"
    )
    models_parser.add_argument(
        "--asc",
        action="store_true",
        help="Sort in ascending order (default when --sort is used)"
    )
    models_parser.add_argument(
        "--dsc",
        action="store_true",
        help="Sort in descending order"
    )
    
    return main_parser


def main() -> int:
    """
    Main program entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = setup_parsers()
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "configure":
        configure_api_key()
        return 0
    elif args.command == "ls":
        if args.subcommand == "models":
            return cmd_list_models(args)
        else:
            print("Error: Subcommand required for 'ls'. Try 'ls models'.", file=sys.stderr)
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())