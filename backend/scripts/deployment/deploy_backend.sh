#!/usr/bin/env bash
set -e

echo "========================================"
echo "Starting backend deployment..."
echo "========================================"

# Get the script directory and navigate to the backend root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$BACKEND_DIR"

echo "Working directory: $(pwd)"

# Check if we're in a git repository
if [ -d ".git" ]; then
    # Pull the latest code
    echo "Pulling latest code from remote repository..."
    git pull origin main
else
    echo "Warning: Not in a git repository, skipping git pull"
fi

# Check for virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Warning: No virtual environment found (venv or .venv)"
fi

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found"
fi

# Check if systemd services exist before restarting
if systemctl list-units --full -all | grep -Fq "uvicorn.service"; then
    echo "Restarting uvicorn.service..."
    sudo systemctl restart uvicorn.service
    
    echo "----------------------------------------"
    echo "Uvicorn Service Status:"
    sudo systemctl status uvicorn.service --no-pager
else
    echo "Warning: uvicorn.service not found"
fi

if systemctl list-units --full -all | grep -Fq "nginx.service"; then
    echo "Restarting nginx.service..."
    sudo systemctl restart nginx.service
else
    echo "Warning: nginx.service not found"
fi

# Test the health endpoint
echo "----------------------------------------"
echo "Testing FastAPI health endpoint..."
if curl -f http://127.0.0.1:8000/api/v1/health 2>/dev/null; then
    echo "✅ Health endpoint is responding"
else
    echo "❌ Health endpoint is not responding"
fi

echo ""
echo "========================================"
echo "Deployment script completed."
echo "========================================" 