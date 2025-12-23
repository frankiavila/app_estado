@echo off
REM Inicia el servidor Uvicorn con FastAPI en modo debug y guarda logs por fecha
cd /d C:\proyectos\app_estado
call venv\Scripts\activate

REM Obtener la fecha actual en formato YYYY-MM-DD
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (
    set day=%%a
    set month=%%b
    set year=%%c
)
set logdate=%year%-%month%-%day%

REM Borrar logs más antiguos de 7 días
forfiles /p "C:\proyectos\app_estado" /m logs_*.txt /d -7 /c "cmd /c del @file"

REM Arranca Uvicorn en host 0.0.0.0:8000 con reload y debug, guardando logs en archivo con fecha
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug > C:\proyectos\app_estado\logs_%logdate%.txt 2>&1

timeout /t 30 >nul
echo FastAPI iniciado correctamente 🚀
exit
