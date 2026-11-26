#!/bin/bash
# ============================================================
# FORTIVEX AI Sales Agent – One-command startup
# Usage: bash start.sh
# ============================================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   FORTIVEX AI Sales Agent – Starting Up     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# --- Backend ---
echo "▶ Starting FastAPI backend on http://localhost:8000 ..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
  echo "  Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies if needed
pip install -q -r requirements.txt

# Seed sample data if DB is fresh
if [ ! -f "fortivex.db" ]; then
  echo "  Seeding sample data..."
  cd "$PROJECT_DIR"
  bash scripts/seed_data.sh
  cd "$BACKEND_DIR"
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "  Waiting for backend..."
for i in {1..15}; do
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✅ Backend is ready."
    break
  fi
  sleep 1
done

# --- Frontend ---
echo ""
echo "▶ Starting React frontend on http://localhost:5173 ..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "  Installing frontend dependencies..."
  npm install
fi

# Open browser after a short delay (macOS)
(sleep 3 && open http://localhost:5173) &

npm run dev

# Cleanup on exit
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT TERM
