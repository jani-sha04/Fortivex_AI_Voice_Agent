#!/usr/bin/env bash
# Setup Python virtual environment and install dependencies
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🐍 Setting up Python environment..."
cd "$BACKEND_DIR"

python3.12 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Backend dependencies installed!"
echo ""
echo "To start the backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  cp ../.env.example .env  # then edit .env with your keys"
echo "  uvicorn app.main:app --reload --port 8000"
