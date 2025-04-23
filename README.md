# Dotfiles

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/behrangsa/dotfiles/graphs/commit-activity)

A carefully crafted collection of configuration files and utility scripts for Linux systems.

<details>
<summary>Table of Contents</summary>

- [Overview](#overview)
- [Modules](#modules)
- [Installation](#installation)
- [Module Details](#module-details)
  - [Git Configuration](#git-configuration)
  - [Conky Configuration](#conky-configuration)
  - [EmptyBye Utility](#emptybye-utility)
  - [NPM Configuration](#npm-configuration)
- [Requirements](#requirements)
- [License](#license)

</details>

## Overview

This repository contains my personal dotfiles and system configuration tools. Each component is modularized for easy installation and maintenance. I've designed this system to be both functional and adaptable to various Linux environments.

<details>
<summary><h2>Modules</h2></summary>

The following modules are included in this repository:

- **git**: Git configuration with useful aliases and default settings
- **conky**: System monitoring configuration with a Vim tips display feature
- **emptybye**: Utility script for finding and removing empty directories
- **npmrc**: npm configuration management with secure token handling

</details>

<details>
<summary><h2>Installation</h2></summary>

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

# Install just the npm configuration
./npmrc/install.sh
```

</details>

<details>
<summary><h2>Module Details</h2></summary>

### Git Configuration

<details>
<summary>Expand Git Configuration Details</summary>

The git module provides:

- Useful aliases for common git operations
- Sensible default settings
- Automatic remote setup

The installer will create a symbolic link from `~/.gitconfig` to the configuration file in this repository.

</details>

### Conky Configuration

<details>
<summary>Expand Conky Configuration Details</summary>

The conky module includes:

- System monitoring dashboard
- CPU, memory, and disk usage statistics
- Temperature monitoring
- Integration with a Vim tips display feature

The installer will create symbolic links to the configuration files and ensure the Vim tips processor script is executable.

</details>

### EmptyBye Utility

<details>
<summary>Expand EmptyBye Utility Details</summary>

EmptyBye is a Python utility that finds and removes empty directories:

- Performs a depth-first search to identify truly empty directories
- Provides a dry-run option to preview changes
- Handles permission errors gracefully

The installer will create a symbolic link to the script in `~/.local/bin`.

</details>

### NPM Configuration

<details>
<summary>Expand NPM Configuration Details</summary>

The npmrc module manages your npm configuration:

- Securely manages npm authentication tokens
- Configures registry settings and defaults
- Sets up package initialization defaults
- Maintains proper file permissions (600) for security

The installer will create a symbolic link from `~/.npmrc` to the configuration file in this repository, ensuring secure handling of sensitive information.

</details>

</details>

<details>
<summary><h2>Requirements</h2></summary>

- Bash shell
- Python 3 (for the EmptyBye utility)
- Git (for version control and git configuration)
- Conky (for system monitoring)
- Node.js and npm (for npm configuration)

</details>

## License

This project is available under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

<sub>Last updated: April 23, 2025</sub>
