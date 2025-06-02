@echo off
REM Mata cualquier proceso llamado model-server.exe
for /f "tokens=2 delims=," %%A in (
    'tasklist /fi "imagename eq model-server.exe" /nh /fo csv ^| find /I "model-server.exe"'
) do (
    taskkill /PID %%A /F
)
echo Servidor detenido.
pause
