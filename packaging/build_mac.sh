#!/bin/bash
# SPDX-License-Identifier: MIT
# Build AutoDisloc2.app (macOS) and dist/AutoDisloc2_macOS.zip.
#
# The build runs in its own virtual environment with exactly the pinned
# versions of packaging/requirements-build.txt (PySide6-Essentials, i.e. only
# the LGPL-licensed Qt parts), independent of the Python used day to day
# (conda, Homebrew, ...). Environment and build folders live outside the
# repository (default ~/.cache/autodisloc-build-venv and ~/.cache/autodisloc-build;
# override with AUTODISLOC_BUILD_VENV / AUTODISLOC_BUILD_DIR): cloud-synced
# folders (Google Drive, iCloud, OneDrive) create conflict copies such as
# "QtCore 2.framework" while PyInstaller rewrites a bundle. Only the finished
# zip is copied to dist/.
set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)
PY=${PYTHON:-python3}
VENV=${AUTODISLOC_BUILD_VENV:-$HOME/.cache/autodisloc-build-venv}
WORK=${AUTODISLOC_BUILD_DIR:-$HOME/.cache/autodisloc-build}
if [ ! -x "$VENV/bin/python" ]; then
  "$PY" -m venv "$VENV"
fi
"$VENV/bin/python" -m pip install -q --upgrade pip
"$VENV/bin/python" -m pip install -q -r packaging/requirements-build.txt
"$VENV/bin/python" packaging/make_icon.py
rm -rf "$WORK"
mkdir -p "$WORK"
export AUTODISLOC_THIRD_DIR="$WORK/third_party"
"$VENV/bin/python" -m PyInstaller --noconfirm --clean --distpath "$WORK/dist" --workpath "$WORK/build" \
  packaging/AutoDisloc2.spec
# release zip: application, licence, third-party notices, Qt source information
mkdir -p "$WORK/stage" "$ROOT/dist"
cp LICENSE "$WORK/stage/LICENSE.txt"
cp "$WORK/third_party/THIRD-PARTY-NOTICES.txt" "$WORK/third_party/QT-SOURCE.txt" "$WORK/stage/"
cp -R "$WORK/dist/AutoDisloc2.app" "$WORK/stage/"
rm -f "$WORK/AutoDisloc2_macOS.zip"
ditto -c -k --norsrc --noextattr "$WORK/stage" "$WORK/AutoDisloc2_macOS.zip"
cp "$WORK/AutoDisloc2_macOS.zip" "$ROOT/dist/"
echo "Done: $WORK/dist/AutoDisloc2.app and dist/AutoDisloc2_macOS.zip"
