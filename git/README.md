# Git Configuration Module

## Overview

This module provides a standardized Git configuration for consistent development across different environments. It includes useful aliases, default settings, and credential management configurations that enhance Git workflows.

## Features

- **Streamlined Aliases**: Shorthand commands for common Git operations
- **Default Branch Settings**: Configures the default branch name for new repositories
- **Push Settings**: Optimized defaults for pushing changes to remote repositories
- **GitHub Credential Management**: Integration with GitHub CLI for secure authentication
- **User Identity**: Central location to configure your Git identity

## Installation

Run the included installation script to set up the Git configuration:

```bash
./install.sh
```

This will create a symbolic link from `~/.gitconfig` to the configuration file in this module, backing up any existing configuration.

## Configuration Details

### Aliases

| Alias     | Command                                                      | Description                         |
| --------- | ------------------------------------------------------------ | ----------------------------------- |
| `s`, `st` | `status`                                                     | Check repository status             |
| `c`, `cm` | `commit`                                                     | Create a commit                     |
| `co`      | `checkout`                                                   | Switch branches or restore files    |
| `br`      | `branch`                                                     | List, create, or delete branches    |
| `lg`      | `log --oneline --graph --decorate --all --author-date-order` | View decorated commit history graph |
| `last`    | `log -1 HEAD`                                                | Show the last commit                |
| `unstage` | `reset HEAD --`                                              | Remove files from staging area      |

### Default Settings

- Default branch name set to `master`
- Push settings configured for seamless remote repository setup
- GitHub credential helper configured to use GitHub CLI
- Terminal output configured to use `cat` as pager for more concise display

## Customization

To customize your Git configuration:

1. Edit the `.gitconfig` file in this directory
2. Run the installation script again to update the symlink

## Integration with GitHub CLI

This configuration uses GitHub CLI for credentials, ensuring:

- Secure authentication with GitHub
- Consistent credentials across terminal sessions
- Support for 2FA and tokens

## Requirements

- GitHub CLI (`gh`) for credential management
- Standard Linux/macOS environment

## Troubleshooting

If you encounter issues with the Git configuration:

1. Verify the symlink is correctly established: `ls -la ~/.gitconfig`
2. Check that GitHub CLI is properly installed: `gh --version`
3. Ensure proper permissions on the configuration files

## License

This module is part of the dotfiles collection and follows the same licensing terms.
