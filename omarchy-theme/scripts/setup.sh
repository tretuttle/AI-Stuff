#!/bin/bash
# Setup script for omarchy-theme plugin
# Installs required dependencies: hellwal (palette extraction) and tint (image recoloring)

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(realpath "$0")")")}"
BIN_DIR="${PLUGIN_ROOT}/bin"

echo "Setting up omarchy-theme plugin..."

# Install hellwal via omarchy's AUR helper
if ! command -v hellwal &>/dev/null; then
    if ! command -v omarchy-pkg-aur-add &>/dev/null; then
        echo "Error: omarchy-pkg-aur-add not found. Install hellwal manually:"
        echo "  yay -S hellwal  # or paru -S hellwal"
        exit 1
    fi
    echo "Installing hellwal..."
    omarchy-pkg-aur-add hellwal
else
    echo "hellwal already installed"
fi

# Create bin directory if needed
mkdir -p "$BIN_DIR"

# Download tint binary
if [[ ! -x "${BIN_DIR}/tint" ]]; then
    echo "Downloading tint..."
    TINT_VERSION="v0.1.7"
    TINT_URL="https://github.com/ashish0kumar/tint/releases/download/${TINT_VERSION}/tint_linux_x86_64.tar.gz"

    curl -sL "$TINT_URL" | tar xz -C "$BIN_DIR"
    chmod +x "${BIN_DIR}/tint"

    # Verify download succeeded
    if ! "${BIN_DIR}/tint" --version &>/dev/null; then
        echo "Error: tint download failed or binary is corrupted"
        exit 1
    fi

    echo "tint installed to ${BIN_DIR}/tint"
else
    echo "tint already installed"
fi

echo "Setup complete!"
echo "  hellwal: $(command -v hellwal)"
echo "  tint: ${BIN_DIR}/tint"
