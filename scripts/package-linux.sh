#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$project_dir"
python_bin=${PYTHON:-python3}
arch=$(uname -m)
case "$arch" in x86_64|aarch64) ;; *) echo "Unsupported architecture: $arch" >&2; exit 1;; esac
"$python_bin" -m PyInstaller --noconfirm --clean --onedir --windowed \
  --name stat-tracker \
  --add-data 'stat_tracker.png:.' \
  --add-data 'assets/branding/straconis-software-wordmark.png:assets/branding' app.py
stage="dist/stat-tracker-linux-$arch"
mkdir -p "$stage"
cp -a dist/stat-tracker/. "$stage/"
cp README.md "$stage/README.md"
# Nexus rejects archive symlinks; dereference PyInstaller's library links when packing.
tar --dereference --hard-dereference -czf "dist/stat-tracker-linux-$arch.tar.gz" -C dist "stat-tracker-linux-$arch"
(cd dist && sha256sum "stat-tracker-linux-$arch.tar.gz" > SHA256SUMS.txt)
