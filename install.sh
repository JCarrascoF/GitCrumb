#!/usr/bin/env bash
# =============================================================================
# install.sh — Create global "gitcrumb" alias
# Usage:
#   ./install.sh              # creates the symlink
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.local/bin/gitcrumb"
XDG_DIR="$HOME/.config/gitcrumb"
CONFIG_FILE="$XDG_DIR/config"

msg_path_missing()    { [[ "$LANG" == "es" ]] && echo "~/.local/bin no está en PATH." || echo "~/.local/bin is not in PATH."; }
msg_add_path()        { [[ "$LANG" == "es" ]] && echo "Añádelo a tu shell config (~/.zshrc, ~/.bash_profile):" || echo "Add it to your shell config (~/.zshrc, ~/.bash_profile):"; }
msg_done()            { [[ "$LANG" == "es" ]] && echo "✓  gitcrumb instalado → $TARGET" || echo "✓  gitcrumb installed → $TARGET"; }
msg_try()             { [[ "$LANG" == "es" ]] && echo "   Prueba: gitcrumb --help" || echo "   Try: gitcrumb --help"; }

# Ensure ~/.local/bin exists and is in PATH
mkdir -p "$HOME/.local/bin"

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠  $(msg_path_missing)"
    echo "   $(msg_add_path)"
    echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

# Create absolute symlink
ln -sf "$SCRIPT_DIR/_gitcrumb_entry.py" "$TARGET"
echo "$(msg_done)"
echo "$(msg_try)"

# ── Optional language config ────────────────────────────────
echo ""
read -r -p "Set UI language? [en/es/none] (default: none): " CHOICE
CHOICE="${CHOICE:-none}"

if [[ "$CHOICE" == "es" || "$CHOICE" == "en" ]]; then
    mkdir -p "$XDG_DIR"
    cat > "$CONFIG_FILE" <<EOF
# gitcrumb config — edit this file to change settings
lang = ${CHOICE}
EOF
    echo "✓  Language set to '${CHOICE}' → $CONFIG_FILE"
fi

echo ""
echo "Tip: create/edit ~/.config/gitcrumb/config anytime."
echo "  lang = es   # Spanish UI"
echo "  lang = en   # English UI (default)"
