#!/bin/bash

# This script assumes you're on a Linux system.

set -euo pipefail

REPO="modal-labs/overeasy"
TARGET="x86_64-unknown-linux-gnu"

echo "Downloading overeasy..."
TAG=$(curl -fsSLI -o /dev/null -w '%{url_effective}' "https://github.com/$REPO/releases/latest" | sed 's|.*/tag/||')
mkdir -p ~/.local/bin
curl -fsSL "https://github.com/$REPO/releases/download/$TAG/overeasy-$TAG-$TARGET.tar.gz" | tar -xz -C ~/.local/bin overeasy
chmod +x ~/.local/bin/overeasy
echo -e "\tInstalled to ~/.local/bin/overeasy"

echo -e "\nVerifying installation... "
echo -e "\tovereasy --version"

echo -e "\t$("$HOME/.local/bin/overeasy" --version)"

# Alias as "oe" to "overeasy" via soft link
ln -sf ~/.local/bin/overeasy ~/.local/bin/oe


case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo -e "\nNote: ~/.local/bin is not on your PATH, add it with:"
     echo -e "\texport PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

echo -e "\n🍳 Overeasy installed, get started with:"
echo -e "\tovereasy --help"
echo -e "\toe --help"
