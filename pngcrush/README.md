# PNGCrush Utility Wrapper

A command-line tool to batch-optimize all PNG files in the current directory
using `pngcrush` with best-practice options. Outputs optimized files
as `<filename>.ready.png`.

## Features

- **Batch Processing**: Runs `pngcrush` over all PNG files in the current directory
- **Safe Output**: Skips files already ending with `.ready.png` to avoid recursion
- **Production-Ready**: Robust error handling, clear output, and safe file handling
- **Easy Installation**: Installs a wrapper script as `crush-pngs` in your `~/.local/bin`

## Installation

Run the install script from this directory:

```bash
./install.sh
```

This will:

- Check for `pngcrush` in your PATH
- Make the script executable
- Symlink it as `crush-pngs` in `~/.local/bin`
- Remind you to add `~/.local/bin` to your PATH if needed

## Dependencies

- `pngcrush` (must be installed and available in your PATH)
- Bash shell

## Usage

```bash
crush-pngs
```

This will process all `.png` files in the current directory, creating optimized versions as `<filename>.ready.png`.

## Example

```bash
crush-pngs
```

## Notes

- Existing `.ready.png` files are skipped.
- The script will exit with an error if `pngcrush` is not installed.
- For advanced usage, edit `crush.sh` as needed.
