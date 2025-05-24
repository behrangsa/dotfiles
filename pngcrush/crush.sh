#!/usr/bin/env bash
# Production-ready: Run pngcrush on all PNG files in the current directory
set -euo pipefail

# Check for pngcrush
if ! command -v pngcrush >/dev/null 2>&1; then
  echo "Error: pngcrush is not installed or not in PATH." >&2
  exit 1
fi

shopt -s nullglob
files=( *.png )
shopt -u nullglob

if [ ${#files[@]} -eq 0 ]; then
  echo "No PNG files found in the current directory."
  exit 0
fi

for f in "${files[@]}"; do
  # Skip files that already have .ready.png suffix
  if [[ "$f" == *.ready.png ]]; then
    continue
  fi
  out="${f%.png}.ready.png"
  echo "Processing '$f' -> '$out'..."
  if ! pngcrush -rem alla -reduce -brute "$f" "$out"; then
    echo "Error processing '$f'" >&2
    exit 2
  fi
  echo "Done: '$out'"
done