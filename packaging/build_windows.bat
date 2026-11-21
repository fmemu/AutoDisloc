@echo off
REM SPDX-License-Identifier: MIT
REM Build AutoDisloc2.exe (Windows). Requires Python 3.9+ (python.org or Anaconda).
REM The build runs in its own virtual environment with exactly the pinned versions of
REM packaging\requirements-build.txt (PySide6-Essentials: only LGPL-licensed Qt parts),
REM outside the repository: %LOCALAPPDATA%\autodisloc-build-venv (override: AUTODISLOC_BUILD_VENV).
cd /d "%~dp0\.."
if "%AUTODISLOC_BUILD_VENV%"=="" set "AUTODISLOC_BUILD_VENV=%LOCALAPPDATA%\autodisloc-build-venv"
if not exist "%AUTODISLOC_BUILD_VENV%\Scripts\python.exe" python -m venv "%AUTODISLOC_BUILD_VENV%" || goto :error
set "VPY=%AUTODISLOC_BUILD_VENV%\Scripts\python.exe"
"%VPY%" -m pip install -q --upgrade pip || goto :error
"%VPY%" -m pip install -q -r packaging\requirements-build.txt || goto :error
"%VPY%" packaging\make_icon.py || goto :error
"%VPY%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\AutoDisloc2.spec || goto :error
echo Done: dist\AutoDisloc2\AutoDisloc2.exe
pause
exit /b 0
:error
echo Build failed.
pause
exit /b 1
