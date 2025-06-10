#!/bin/bash

echo "🚀 Launching FastAPI app..."
source venv/bin/activate
uvicorn main:app --reload
