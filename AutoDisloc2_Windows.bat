@echo off
REM Run AutoDisloc 2 from source on Windows (double-click). Installs missing packages once.
cd /d "%~dp0"
python -c "import PySide6, scipy, matplotlib, pandas, openpyxl" 2>nul || python -m pip install -r requirements.txt
start "" pythonw AutoDisloc2.py
