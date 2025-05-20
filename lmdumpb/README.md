# LMDB Database Dump Utility

A command-line utility to export data from Zed's LMDB (Lightning Memory-Mapped Database) databases.

## Features

- **Data Export**: Dumps records from a specified LMDB database. It specifically looks for a database named "threads" but falls back to the default database if "threads" is not found.
- **Multiple Output Formats**:
  - **JSON**: Outputs the data as a JSON array of records.
  - **HTML**: Generates a structured HTML document, detailing records, messages, segments, and tool interactions based on a known schema (e.g., Zed's assistant conversation schema).
  - **Markdown**: Creates a structured Markdown document, similar to the HTML output, suitable for documentation or easy reading.
- **Customizable Output File**: Allows users to specify an output file path. If not specified, it defaults to `./<dbname>-dump.<format_extension>` in the current directory.
- **User-Friendly Interface**: Simple and straightforward command-line arguments.
- **Data Deserialization**: Attempts to decode UTF-8 values and parse them as JSON. Errors during deserialization of individual records are logged, and the script continues processing other records.

## Installation

The script can be made executable and placed in a directory within your system's `PATH`. For example, using an `install.sh` script (if provided, or manually):

```bash
cd ~/dotfiles/lmdumpb
./install.sh
```

This might create a symbolic link (e.g., `lmdb-dump`) in a directory like `~/.local/bin`. Ensure this directory is in your `PATH`.

### Dependencies

The script requires Python 3 and the following Python package (which might need to be installed manually if not present, e.g., using `pip3`):

- `python-lmdb`: For LMDB database interaction.

## Usage

```bash
lmdb-dump [OPTIONS]
```

### Arguments

- `-d/--db DB_PATH`: (Required) Path to the LMDB database directory.
- `-o/--output OUTPUT_FILE_PATH`: (Optional) Full path for the output file. Defaults to `./<db_name>-dump.<format>` in the current directory (e.g., `./mydb-dump.json`, `./mydb-dump.html`, `./mydb-dump.md`).
- `-f/--format FORMAT`: (Optional) Output format. Choices are `json`, `html`, `markdown`. Defaults to `json`.

## Examples

### Basic Usage (Default JSON Output)

```bash
# Export data from 'my_lmdb_data_dir' to 'my_lmdb_data_dir-dump.json' in the current directory
lmdb-dump --db ./my_lmdb_data_dir
```

### HTML Output

```bash
# Export data to an HTML file in the current directory
lmdb-dump --db ./my_lmdb_data_dir --format html
```

This will create `my_lmdb_data_dir-dump.html`.

### Markdown Output

```bash
# Export data to a Markdown file in the current directory
lmdb-dump --db ./my_lmdb_data_dir --format markdown
```

This will create `my_lmdb_data_dir-dump.md`.

### Specifying Output File Path

```bash
# Export data from 'my_lmdb_data_dir' to a specific HTML file
lmdb-dump --db ./my_lmdb_data_dir --format html --output ./exports/my_custom_dump.html
```

This will create `my_custom_dump.html` inside the `exports` directory (which will be created if it doesn't exist).

## Error Handling

The script includes basic error handling for:

- Non-existent or invalid LMDB database paths.
- Issues creating the output directory or writing to the output file.
- Problems connecting to or reading from the LMDB database.
- Errors during deserialization of individual records (these are logged as warnings, and the script attempts to continue).
  Error messages are printed to standard output/error.

## Output Files

The content and structure of the output files depend on the chosen format:

### JSON Output (`--format json`)

- A single JSON file containing an array of records. Each record corresponds to an item in the LMDB, parsed as a JSON object.

### HTML Output (`--format html`)

- A single HTML file.
- Includes a title with the source LMDB database name.
- Displays each record with its main properties (e.g., `summary`, `version`, `updated_at`).
- Details `messages`, `segments`, `tool_uses`, and `tool_results` in a structured and readable HTML format, based on the expected schema of the data.
- Includes basic inline CSS for readability.

### Markdown Output (`--format markdown`)

- A single Markdown file.
- Includes a main title with the source LMDB database name.
- Each record is presented with its main properties.
- `messages`, `segments`, `tool_uses`, and `tool_results` are formatted using Markdown headings, lists, and code blocks for clarity.
