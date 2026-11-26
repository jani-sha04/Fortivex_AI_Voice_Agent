# ============================================================
# FORTIVEX AI Sales Agent – Makefile
# ============================================================

BACKEND_DIR  := backend
FRONTEND_DIR := frontend
VENV         := $(BACKEND_DIR)/venv
PYTHON       := $(VENV)/bin/python3
PIP          := $(VENV)/bin/pip
UVICORN      := $(VENV)/bin/uvicorn

.PHONY: help install install-backend install-frontend seed test \
        start start-backend start-frontend build lint clean whisper piper

# Default target
help:
	@echo ""
	@echo "FORTIVEX AI Sales Agent – Available Commands"
	@echo "--------------------------------------------"
	@echo "  make install         Install all dependencies (backend + frontend)"
	@echo "  make install-backend Install Python dependencies"
	@echo "  make install-frontend Install Node.js dependencies"
	@echo "  make seed            Seed sample data into the database"
	@echo "  make test            Run all backend tests"
	@echo "  make start           Start backend + frontend together"
	@echo "  make start-backend   Start FastAPI backend only (port 8000)"
	@echo "  make start-frontend  Start React dev server only (port 5173)"
	@echo "  make build           Build frontend for production"
	@echo "  make whisper         Set up whisper.cpp (builds from source)"
	@echo "  make piper           Set up Piper TTS (downloads binary)"
	@echo "  make clean           Remove build artifacts and caches"
	@echo ""

## ── Installation ─────────────────────────────────────────────────────────────

install: install-backend install-frontend
	@echo "✅ All dependencies installed."

install-backend:
	@echo "▶ Setting up Python virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt -q
	@echo "✅ Backend dependencies installed."

install-frontend:
	@echo "▶ Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "✅ Frontend dependencies installed."

## ── Database ──────────────────────────────────────────────────────────────────

seed:
	@echo "▶ Seeding sample data..."
	bash scripts/seed_data.sh
	@echo "✅ Sample data seeded."

## ── Testing ───────────────────────────────────────────────────────────────────

test:
	@echo "▶ Running backend tests..."
	cd $(BACKEND_DIR) && DEMO_MODE=true GEMINI_API_KEY=dummy \
	    $(VENV)/bin/pytest tests/test_api.py -v --tb=short
	@echo "✅ Tests complete."

## ── Run ───────────────────────────────────────────────────────────────────────

start: start-backend start-frontend

start-backend:
	@echo "▶ Starting FastAPI backend on http://localhost:8000 ..."
	cd $(BACKEND_DIR) && source venv/bin/activate && \
	    $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

start-frontend:
	@echo "▶ Starting React frontend on http://localhost:5173 ..."
	cd $(FRONTEND_DIR) && npm run dev

## ── Build ─────────────────────────────────────────────────────────────────────

build:
	@echo "▶ Building frontend for production..."
	cd $(FRONTEND_DIR) && npm run build
	@echo "✅ Frontend built → frontend/dist/"

## ── Voice Tools ───────────────────────────────────────────────────────────────

whisper:
	@echo "▶ Setting up whisper.cpp..."
	bash scripts/setup_whisper.sh

piper:
	@echo "▶ Setting up Piper TTS..."
	bash scripts/setup_piper.sh

## ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	@echo "▶ Cleaning build artifacts..."
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/.vite
	rm -rf $(BACKEND_DIR)/__pycache__ $(BACKEND_DIR)/app/__pycache__
	find $(BACKEND_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean complete."
