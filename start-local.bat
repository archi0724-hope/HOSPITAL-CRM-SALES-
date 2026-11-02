@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run: uv venv --python 3.12 .venv
  echo Then: uv pip install --python .venv\Scripts\python.exe -r sales-ops\requirements.txt
  pause
  exit /b 1
)
".venv\Scripts\python.exe" run_local.py
