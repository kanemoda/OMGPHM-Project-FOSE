@echo off
echo 🚀 Launching FastAPI app...
call venv\Scripts\activate.bat
uvicorn main:app --reload
pause