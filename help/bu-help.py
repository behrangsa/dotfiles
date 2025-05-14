#!/usr/bin/env python3
"""
bu-help.py - A utility for getting help on various subjects using OpenAI

This script sends queries to OpenAI with a customized system prompt based on the
specified subject, streaming the response back to the user.

Usage:
    bu-help.py --subject vim --prompt "How can I show line numbers in vim, persistently"

Author: Behrang Saeedzadeh
License: MIT
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
import textwrap
from typing import Dict, Any, Optional, Iterator, Union

# Constants
API_BASE_URL = "https://api.openai.com/v1/chat/completions"
CONFIG_DIR = Path.home() / ".config" / "openai"
CONFIG_FILE = CONFIG_DIR / "config"
API_KEY_ENV_VAR = "_OPENAI_API_KEY"
DEFAULT_MODEL = "gpt-4o"

# ANSI color codes for terminal output
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "cyan": "\033[36m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "green": "\033[32m",
}

# Pre-defined system prompts for different subjects
SYSTEM_PROMPTS = {
    "vim": "You are a vim expert and tutor",
    "bash": "You are a bash scripting expert and Linux command line tutor",
    "git": "You are a git expert and version control system tutor",
    "python": "You are a Python programming expert and tutor",
    "linux": "You are a Linux system administration expert and tutor",
    "docker": "You are a Docker and container expert and tutor",
    "kubernetes": "You are a Kubernetes expert and cloud-native application tutor",
    "aws": "You are an AWS cloud services expert and tutor",
    "javascript": "You are a JavaScript programming expert and tutor",
    "sql": "You are a SQL and database expert and tutor",
    "regex": "You are a regular expressions expert and tutor",
}

# Terminal width for wrapping text
TERMINAL_WIDTH = os.get_terminal_size().columns if sys.stdout.isatty() else 80


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


def stream_openai_response(system_prompt: str, user_prompt: str, api_key: str, model: str = DEFAULT_MODEL) -> Iterator[str]:
    """
    Stream a response from OpenAI's chat completion API.
    
    Args:
        system_prompt: The system message that sets the assistant's behavior
        user_prompt: The user's query
        api_key: OpenAI API key
        model: The model to use for completion
        
    Yields:
        Chunks of the response text as they are received
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True
    }
    
    try:
        response = requests.post(
            API_BASE_URL,
            headers=headers,
            json=data,
            stream=True
        )
        response.raise_for_status()
        
        # Process the streaming response
        for line in response.iter_lines():
            if line:
                # Remove the "data: " prefix
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # Skip "data: "
                    
                    # Skip the [DONE] message
                    if line == "[DONE]":
                        break
                        
                    try:
                        # Parse the JSON response
                        json_response = json.loads(line)
                        
                        # Extract the content delta if it exists
                        delta = json_response.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        # Skip lines that aren't valid JSON
                        continue
    except requests.RequestException as e:
        error_msg = f"Error communicating with OpenAI API: {e}\n"
        
        # Try to extract more detailed error information
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if 'error' in error_data and 'message' in error_data['error']:
                    error_msg += f"API Error: {error_data['error']['message']}"
            except (ValueError, KeyError):
                pass
        
        yield f"{COLORS['red']}{error_msg}{COLORS['reset']}"


def print_header(subject: str, prompt: str) -> None:
    """
    Print a formatted header with the subject and prompt.
    
    Args:
        subject: The subject being queried
        prompt: The user's prompt
    """
    print(f"\n{COLORS['bold']}{COLORS['cyan']}=== bu-help: {subject.upper()} ==={COLORS['reset']}")
    print(f"{COLORS['yellow']}Q: {prompt}{COLORS['reset']}\n")


def get_subject_prompt(subject: str) -> str:
    """
    Get the system prompt for a given subject.
    
    Args:
        subject: The subject name
        
    Returns:
        The system prompt for the subject, or a generic prompt if not found
    """
    # Check if we have a pre-defined prompt for this subject
    if subject.lower() in SYSTEM_PROMPTS:
        return SYSTEM_PROMPTS[subject.lower()]
    
    # Otherwise, create a generic prompt
    return f"You are a {subject} expert and tutor"


def main() -> int:
    """
    Main program entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Get help on various subjects using OpenAI"
    )
    
    parser.add_argument(
        "--subject", "-s",
        required=True,
        help="The subject to get help on (e.g., vim, bash, git)"
    )
    
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="The help query or prompt"
    )
    
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"The OpenAI model to use (default: {DEFAULT_MODEL})"
    )
    
    parser.add_argument(
        "--key", "-k",
        help="OpenAI API key (overrides env var and config file)"
    )
    
    args = parser.parse_args()
    
    # Get the API key
    api_key = args.key or get_api_key()
    if not api_key:
        print(f"{COLORS['red']}Error: OpenAI API key not found. Please set the {API_KEY_ENV_VAR} environment variable, "  
              f"provide it with --key, or configure it with 'bu-openai configure'.{COLORS['reset']}", 
              file=sys.stderr)
        return 1
    
    # Get the system prompt for the subject
    system_prompt = get_subject_prompt(args.subject)
    
    # Print the header
    print_header(args.subject, args.prompt)
    
    # Stream the response
    try:
        full_response = ""
        for chunk in stream_openai_response(system_prompt, args.prompt, api_key, args.model):
            full_response += chunk
            print(chunk, end="", flush=True)
        print("\n")
    except KeyboardInterrupt:
        print(f"\n{COLORS['yellow']}Response streaming interrupted by user.{COLORS['reset']}")
        return 130  # Standard exit code for SIGINT
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
