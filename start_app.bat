@echo off
REM Inicia el servidor Uvicorn con FastAPI en modo debug
cd /d C:\proyectos\app_estado
call venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8080
start "" cmd /c "uvicorn main:app --reload --log-level debug"
timeout /t 30 >nul
echo FastAPI iniciado correctamente 🚀
exit