#!/bin/bash
# run.sh - Quick start script for LegalAI Pro

echo "Starting LegalAI Pro Backend Server..."
echo "=================================="

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
cd backend
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads
mkdir -p vectorstore

# Start the server
echo "Starting Flask server..."
echo "Frontend will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo "=================================="