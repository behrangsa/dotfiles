# Dotfiles

A carefully crafted collection of configuration files and utility scripts for Linux systems.

## Overview

This repository contains my personal dotfiles and system configuration tools. Each component is modularized for easy installation and maintenance. I've designed this system to be both functional and adaptable to various Linux environments.

## Modules

The following modules are included in this repository:

- **git**: Git configuration with useful aliases and default settings
- **conky**: System monitoring configuration with a Vim tips display feature
- **emptybye**: Utility script for finding and removing empty directories

## Installation

The repository includes a master installation script that will automatically detect and install all modules.

```bash
git clone https://github.com/behrangsa/dotfiles.git
cd dotfiles
./install.sh
```

You can also install individual modules by running their respective installation scripts:

```bash
# Install just the git configuration
./git/install.sh

# Install just the conky configuration
./conky/install.sh

# Install just the emptybye utility
./emptybye/install.sh
```

## Module Details

### Git Configuration

The git module provides:
- Useful aliases for common git operations
- Sensible default settings
- Automatic remote setup

The installer will create a symbolic link from `~/.gitconfig` to the configuration file in this repository.

### Conky Configuration

The conky module includes:
- System monitoring dashboard
- CPU, memory, and disk usage statistics
- Temperature monitoring
- Integration with a Vim tips display feature

The installer will create symbolic links to the configuration files and ensure the Vim tips processor script is executable.

### EmptyBye Utility

EmptyBye is a Python utility that finds and removes empty directories:
- Performs a depth-first search to identify truly empty directories
- Provides a dry-run option to preview changes
- Handles permission errors gracefully

The installer will create a symbolic link to the script in `~/.local/bin`.

## Requirements

- Bash shell
- Python 3 (for the EmptyBye utility)
- Git (for version control and git configuration)
- Conky (for system monitoring)

## License

This project is available under the MIT License.