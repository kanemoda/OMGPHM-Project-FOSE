#!/bin/bash

echo "🚀 Starting full setup for the restaurant system..."

# Step 1: Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 not found. Please install Python 3 and rerun this script."
    exit 1
fi

# Step 2: Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "🔁 Virtual environment already exists."
fi

# Step 3: Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Step 4: Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Step 5: Install dependencies
echo "📦 Installing dependencies..."
pip install fastapi uvicorn jinja2 sqlalchemy python-multipart

# Optional: Create a requirements.txt for future use
echo "📄 Exporting requirements.txt..."
pip freeze > requirements.txt

echo "🎉 Setup complete! You can now run the app with ./start.sh"
