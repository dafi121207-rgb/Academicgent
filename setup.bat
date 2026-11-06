@echo off
setlocal
cd /d "%~dp0"
py -3 --version >nul 2>&1
if errorlevel 1 (
  echo Pasang Python 3.11 atau lebih baru, kemudian buka setup.bat lagi.
  pause
  exit /b 1
)
py -3 -m venv .venv
if errorlevel 1 goto failed
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Setup selesai. Buka start.bat untuk menjalankan Academicgent.
pause
exit /b 0
:failed
echo Setup gagal. Periksa pesan di atas dan koneksi internet, lalu coba lagi.
pause
exit /b 1
