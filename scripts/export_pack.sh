#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${1:-$ROOT_DIR/dist}"
mkdir -p "$OUT_DIR"

VERSION="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="$OUT_DIR/agentic-sdlc-pack-$VERSION.tar.gz"

tar -czf "$ARCHIVE" -C "$(dirname "$ROOT_DIR")" "$(basename "$ROOT_DIR")"

echo "PACK_ARCHIVE=$ARCHIVE"
