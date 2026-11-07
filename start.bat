@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Jalankan setup.bat dahulu.
  pause
  exit /b 1
)
call start_buddy.bat
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
if errorlevel 1 pause
