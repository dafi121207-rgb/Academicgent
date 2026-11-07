@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\pythonw.exe (
  echo Jalankan setup.bat dahulu.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -c "import tkinter; from PIL import ImageTk"
if errorlevel 1 (
  echo Pasang dukungan Tcl/Tk melalui Modify pada installer Python, lalu coba lagi.
  pause
  exit /b 1
)
start "Academicgent buddy" .venv\Scripts\pythonw.exe desktop_buddy.py
