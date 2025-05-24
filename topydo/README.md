# topydo

Configuration and customization for the [topydo](https://github.com/topydo/topydo) CLI todo.txt manager.

## Description

The `topydo` module provides a curated configuration for topydo, including:

- A main configuration file (`config`) with color and file settings
- A `columns` file defining custom views and filters for your tasks

## Prerequisites

- [topydo](https://github.com/topydo/topydo) installed
- A `~/Todos/` directory (or adjust the `filename` and `archive_filename` in `config`)

## Installation

The module will be installed automatically when running the main dotfiles install script:

```bash
./install.sh
```

Or, to install just the topydo module:

```bash
cd topydo
./install.sh
```

This will create symbolic links from `~/.config/topydo/config` and `~/.config/topydo/columns` to this module's files.

## Features

### Configuration (`config`)

- Sets the todo.txt and archive file locations
- Enables 256-color support
- Customizes focus background color

### Columns (`columns`)

- Predefined views: All tasks, Due today, Overdue, Chores, Reading list
- Custom filters and sorting for each view

## Customization

To modify settings, edit the `config` and `columns` files in this directory. Changes will be reflected the next time you run topydo.

## Notes

- Ensure the paths in `config` exist or are updated to your preferred todo.txt location
- For more on custom columns and filters, see the [topydo documentation](https://topydo.readthedocs.io/en/latest/)
