#!/bin/bash
# Run AutoDisloc 2 from source on macOS (double-click). Installs missing packages once.
cd "$(dirname "$0")"
PY=python3
[ -x /opt/anaconda3/bin/python3 ] && PY=/opt/anaconda3/bin/python3
$PY -c "import PySide6, scipy, matplotlib, pandas, openpyxl" 2>/dev/null || $PY -m pip install -r requirements.txt
$PY AutoDisloc2.py
