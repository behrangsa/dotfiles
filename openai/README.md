# OpenAI CLI Utility

A streamlined command-line interface for interacting with OpenAI's API services. This module provides a user-friendly way to manage and explore OpenAI's models and other resources.

## Features

- **Model Information**: List and explore available OpenAI models
- **Flexible Output Formats**: Display data as JSON or formatted tables
- **Advanced Filtering**: Filter models by name or other attributes
- **Sorting Options**: Sort results by various fields (ID, creation date, owner)
- **Pretty Formatting**: Human-readable date formatting and syntax highlighting
- **Secure Authentication**: Proper API key management with secure storage

## Installation

The module is installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

You can also install it standalone:

```bash
cd ~/dotfiles/openai
./install.sh
```

### Dependencies

The script requires Python 3 and the following Python packages (automatically installed):

- `requests`: For API communication
- `pygments`: For syntax highlighting
- `rich`: For table formatting and terminal styling

## Usage

```bash
bu-openai [OPTIONS] COMMAND [ARGS]
```

### Commands

- `configure`: Set up your OpenAI API key
- `ls models`: List available OpenAI models

### Global Options

- `-k/--key KEY`: Specify an OpenAI API key for a single command
- `-v/--version`: Show version information

### Model Listing Options

- `-t/--table`: Display results in a tabular format
- `-c/--compact`: Output compact JSON (without pretty printing)
- `-d/--pretty-dates`: Format timestamps as dates (YYYY-MM-DD)
- `--no-color`: Disable colorized output
- `-f/--filter PATTERN`: Filter models by name (case-insensitive)
- `--sort {id,object,created,owned_by}`: Sort by specified field
- `--asc`: Sort in ascending order (default)
- `--dsc`: Sort in descending order

## Examples

### Basic Usage

```bash
# Configure your API key
bu-openai configure

# List all available models as pretty-printed JSON
bu-openai ls models

# List models in table format
bu-openai ls models --table
```

### Advanced Filtering and Sorting

```bash
# Filter models containing 'gpt'
bu-openai ls models --filter gpt

# List GPT models sorted by creation date in descending order (newest first)
bu-openai ls models --filter gpt --sort created --dsc

# List models with readable dates in table format
bu-openai ls models --table --pretty-dates --sort id
```

## Configuration

Your API key is stored in `~/.config/openai/config` with secure file permissions (600) to prevent unauthorized access. You can also provide an API key for individual commands using the `-k/--key` option.

## Security

- API keys are stored with secure file permissions (only readable by your user)
- The config directory has restricted permissions (700)
