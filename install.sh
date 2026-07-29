#!/usr/bin/env bash
# =============================================================================
# install.sh — Create global "gitrack" alias
# Usage:
#   ./install.sh              # creates the symlink
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.local/bin/gitrack"

# Ensure ~/.local/bin exists and is in PATH
mkdir -p "$HOME/.local/bin"

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠  ~/.local/bin no está en PATH."
    echo "   Añádelo a tu shell config (~/.zshrc, ~/.bash_profile):"
    echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

# Create absolute symlink
ln -sf "$SCRIPT_DIR/_gitrack_entry.py" "$TARGET"
echo "✓  gitrack instalado → $TARGET"
echo "   Prueba: gitrack --help"
