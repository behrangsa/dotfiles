# SQLite Database Dump Utility

A command-line utility to export tables from an SQLite database to individual HTML files. This module provides a simple way to inspect and share SQLite database contents in a human-readable format.

## Features

- **Table Export**: Dumps all tables from a specified SQLite database.
- **HTML Output**: Saves each table as a separate HTML file.
- **Customizable Output**: Allows users to specify an output directory for the exported files.
- **User-Friendly Interface**: Simple and straightforward command-line arguments.

## Installation

The module is installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

You can also install it standalone:

```bash
cd ~/dotfiles/sqlite
./install.sh
```

### Dependencies

The script requires Python 3 and the following Python package (automatically installed if missing by `install.sh`):

- `pandas`: For data manipulation and HTML export.
- `sqlite3`: (Usually included with Python standard library) For SQLite database interaction.

## Usage

```bash
bu-sqlite-dump [OPTIONS]
```

### Arguments

- `-d/--db DB_PATH`: (Required) Path to the SQLite database file.
- `-o/--output OUTPUT_DIR`: (Optional) Directory to save the HTML files. Defaults to the current directory.

## Examples

### Basic Usage

```bash
# Export tables from 'mydatabase.db' to the current directory
bu-sqlite-dump --db mydatabase.db
```

### Specifying Output Directory

```bash
# Export tables from 'mydatabase.db' to a directory named 'db_export'
bu-sqlite-dump --db mydatabase.db --output ./db_export
```

## Error Handling

The script includes basic error handling for:

- Non-existent database files.
- Issues creating the output directory.
- Problems connecting to or querying the database.
  Error messages are printed to standard error.
