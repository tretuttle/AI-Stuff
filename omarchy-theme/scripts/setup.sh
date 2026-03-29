#!/bin/bash
# Setup script for omarchy-theme plugin
# Installs required dependencies: hellwal (palette extraction) and tint (image recoloring)

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(realpath "$0")")")}"
BIN_DIR="${PLUGIN_ROOT}/bin"

echo "Setting up omarchy-theme plugin..."

# Create bin directory if needed
mkdir -p "$BIN_DIR"

# Build hellwal from source (no sudo required)
if [[ ! -x "${BIN_DIR}/hellwal" ]]; then
    echo "Building hellwal from source..."
    HELLWAL_VERSION="1.0.7"
    HELLWAL_URL="https://github.com/danihek/hellwal/archive/refs/tags/v${HELLWAL_VERSION}.tar.gz"

    TEMP_DIR=$(mktemp -d)
    trap "rm -rf $TEMP_DIR" EXIT

    curl -sL "$HELLWAL_URL" | tar xz -C "$TEMP_DIR"
    cd "$TEMP_DIR/hellwal-${HELLWAL_VERSION}"

    cc -Wall -Wextra -O3 hellwal.c -o hellwal -lm -DVERSION=\"${HELLWAL_VERSION}\"
    mv hellwal "${BIN_DIR}/hellwal"
    chmod +x "${BIN_DIR}/hellwal"

    cd - > /dev/null

    if ! "${BIN_DIR}/hellwal" --version &>/dev/null; then
        echo "Error: hellwal build failed"
        exit 1
    fi

    echo "hellwal built and installed to ${BIN_DIR}/hellwal"
else
    echo "hellwal already installed"
fi

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
echo "  hellwal: ${BIN_DIR}/hellwal"
echo "  tint: ${BIN_DIR}/tint"
