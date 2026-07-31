#!/bin/bash

# This script assumes you're on a Linux system.

set -euo pipefail

REPO="modal-labs/overeasy"
TARGET="x86_64-unknown-linux-gnu"

# Choose the install location:
if [ -n "${OVEREASY_INSTALL_DIR:-}" ]; then
  INSTALL_DIR="$OVEREASY_INSTALL_DIR"
elif [ "$(id -u)" -eq 0 ]; then
  INSTALL_DIR="/usr/local/bin"
else
  INSTALL_DIR="$HOME/.local/bin"
fi

echo "Downloading overeasy..."
mkdir -p "$INSTALL_DIR"
curl -fsSL -o "$INSTALL_DIR/overeasy" "https://github.com/$REPO/releases/latest/download/overeasy-$TARGET"
chmod +x "$INSTALL_DIR/overeasy"
echo -e "\tInstalled to $INSTALL_DIR/overeasy"

echo -e "\nVerifying installation... "
echo -e "\tovereasy --version"

echo -e "\t$("$INSTALL_DIR/overeasy" --version)"

# Alias as "oe" to "overeasy" via soft link
ln -sf "$INSTALL_DIR/overeasy" "$INSTALL_DIR/oe"


case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *) echo -e "\nNote: $INSTALL_DIR is not on your PATH, add it with:"
     echo -e "\texport PATH=\"$INSTALL_DIR:\$PATH\"" ;;
esac

echo -e "\n🍳 Overeasy installed, get started with:"
echo -e "\tovereasy --help"
echo -e "\toe --help"
