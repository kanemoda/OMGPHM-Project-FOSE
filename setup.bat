@echo off
echo 🚀 Starting full setup for the restaurant system...

REM Step 1: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ and rerun this script.
    pause
    exit /b 1
)

REM Step 2: Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
) else (
    echo 🔁 Virtual environment already exists.
)

REM Step 3: Activate virtual environment
echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

REM Step 4: Upgrade pip
echo 📈 Upgrading pip...
python -m pip install --upgrade pip

REM Step 5: Install dependencies
echo 📦 Installing dependencies...
pip install fastapi uvicorn jinja2 sqlalchemy python-multipart itsdangerous pytest httpx

REM Optional: Create a requirements.txt for future use
echo 📄 Exporting requirements.txt...
pip freeze > requirements.txt

echo 🎉 Setup complete! You can now run the app with start.bat
pause