@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Python environment not found. Run the setup instructions in README.md first.
  exit /b 1
)

".venv\Scripts\python.exe" "scripts\update_current_season.py"
exit /b %ERRORLEVEL%
