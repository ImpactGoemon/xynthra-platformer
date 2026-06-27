# Running Xynthra

Two ways: from a terminal (needs Python) or as a standalone `.exe` (no Python
needed once built).

## A. Terminal (from source)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```
Or just double-click `run.bat`.

## B. Standalone .exe (PyInstaller)

A Windows `.exe` must be built **on Windows**. From the project folder:

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm Xynthra.spec
```
Or just double-click `build_exe.bat`. The result is **`dist\Xynthra.exe`** — a
single file with the art bundled inside; double-click to play.

Notes:
- The spec sets `console=False` (clean windowed game). If you want a console for
  logs/errors, set `console=True` in `Xynthra.spec` and rebuild.
- `build/` and `dist/` are git-ignored. `Xynthra.spec` is committed.
- The bundled `.exe` contains the GandalfHardcore art (paid pack) — keep it for
  personal use; don't distribute the `.exe` publicly.

## Controls

Enter/Space start - arrows or A/D move - Space jump (hold = higher) -
Down crouch - Esc quit.
