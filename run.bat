@echo off
REM Double-click to run the game from source. Installs deps the first time.
cd /d "%~dp0"
py -m pip install -r requirements.txt
py main.py
pause
