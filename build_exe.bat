@echo off
REM Double-click to build dist\Xynthra.exe. Installs what it needs first.
cd /d "%~dp0"
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm Xynthra.spec
echo.
echo Done. Your game is at:  dist\Xynthra.exe  (double-click to play)
pause
