# Development Container Configuration

## Overview

This directory contains the configuration for a Visual Studio Code Development Container (devcontainer) designed specifically for dotfiles management and development. The devcontainer provides a consistent, isolated environment with all necessary tools pre-installed, ensuring that everyone working on this project has an identical development setup.

## Files

- `devcontainer.json` - The main configuration file that defines the development container properties, extensions, and features
- `Dockerfile` - Defines the custom Docker image used by the devcontainer
- `README.md` - This file, providing documentation about the devcontainer setup

## Features

The devcontainer includes:

- **Ubuntu 24.04** - Latest LTS release as the base operating system
- **Git** - Latest version with PPA support
- **GitHub CLI** - For interacting with GitHub repositories directly from the terminal
- **Docker-in-Docker** - For container management within the devcontainer
- **Oh-My-Zsh** - Enhanced shell experience with customizations
- **Development Tools** - Common utilities like curl, wget, vim, and more
- **Language Support** - Python and Node.js environments

## VS Code Extensions

The devcontainer comes pre-configured with several useful extensions:

- GitHub Copilot and Copilot Chat
- GitHub Pull Request and Issues
- GitLens for advanced Git capabilities
- Prettier for code formatting
- Markdown All-in-One
- YAML support
- Docker integration
- ShellCheck and shell-format for shell script development

## Usage

To use this devcontainer:

1. Ensure you have Docker and Visual Studio Code with the Remote - Containers extension installed
2. Open this repository in VS Code
3. When prompted, select "Reopen in Container"
4. Alternatively, use the Command Palette (F1) and select "Remote-Containers: Reopen in Container"

## Customization

To customize this devcontainer:

- Modify `devcontainer.json` to add/remove features or extensions
- Update `Dockerfile` to install additional packages or modify system configuration

## Best Practices

- Keep the container as lightweight as possible
- Document any significant changes to the devcontainer configuration
- Test changes thoroughly before committing them
- Consider the impact on build time and container size when adding new features

## Troubleshooting

If you encounter issues with the devcontainer:

1. Rebuild the devcontainer using "Remote-Containers: Rebuild Container" from the Command Palette
2. Check Docker logs for errors during container build
3. Verify that your Docker installation is up-to-date
4. Ensure you have sufficient disk space and memory for container operations

## Resources

- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Developing inside a Container](https://code.visualstudio.com/docs/remote/containers)
- [devcontainer.json reference](https://code.visualstudio.com/docs/remote/devcontainerjson-reference)