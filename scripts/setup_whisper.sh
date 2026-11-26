#!/usr/bin/env bash
# ============================================================
# Setup Whisper.cpp for FORTIVEX AI Sales Agent
# Optimized for Apple Silicon M4 with Metal acceleration
# ============================================================
# Usage: bash scripts/setup_whisper.sh
# ============================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
WHISPER_DIR="$BACKEND_DIR/whisper.cpp"

echo ""
echo "🎙️  Setting up Whisper.cpp for Apple Silicon M4..."
echo "   Project root: $PROJECT_ROOT"
echo "   Whisper dir:  $WHISPER_DIR"
echo ""

# ── 1. Clone whisper.cpp if not present ─────────────────────
if [ ! -d "$WHISPER_DIR/.git" ]; then
  echo "📦 Cloning whisper.cpp..."
  git clone https://github.com/ggerganov/whisper.cpp "$WHISPER_DIR"
else
  echo "✓  whisper.cpp already cloned."
  cd "$WHISPER_DIR"
  git pull --rebase origin master 2>/dev/null || true
fi

cd "$WHISPER_DIR"

# ── 2. Build ─────────────────────────────────────────────────
# whisper.cpp has a plain Makefile that works on macOS without cmake.
# WHISPER_METAL=1 enables Apple Metal GPU acceleration on M4.

echo ""
echo "🔨 Building whisper.cpp with Metal acceleration..."
make clean 2>/dev/null || true

NPROC=$(sysctl -n hw.logicalcpu 2>/dev/null || echo 4)

if make WHISPER_METAL=1 -j"$NPROC" 2>&1; then
  echo "✅ Metal build succeeded."
  BINARY="$WHISPER_DIR/main"
else
  echo "⚠️  Metal build failed — trying standard build..."
  make clean 2>/dev/null || true
  make -j"$NPROC" 2>&1
  BINARY="$WHISPER_DIR/main"
fi

# Newer whisper.cpp versions may produce 'whisper-cli' instead of 'main'
if [ ! -f "$BINARY" ] && [ -f "$WHISPER_DIR/whisper-cli" ]; then
  ln -sf "$WHISPER_DIR/whisper-cli" "$BINARY"
  echo "   Linked whisper-cli → main"
fi

if [ ! -f "$BINARY" ]; then
  echo "❌ Build failed: binary not found at $BINARY"
  echo "   Check build output above for errors."
  exit 1
fi

chmod +x "$BINARY"
echo "   Binary: $BINARY"

# ── 3. Download model ─────────────────────────────────────────
MODEL_DIR="$WHISPER_DIR/models"
MODEL_FILE="$MODEL_DIR/ggml-base.en.bin"

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_FILE" ]; then
  echo ""
  echo "📥 Downloading Whisper base.en model (~142MB)..."
  if [ -f "$MODEL_DIR/download-ggml-model.sh" ]; then
    bash "$MODEL_DIR/download-ggml-model.sh" base.en
  else
    # Direct download fallback
    MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    curl -L --progress-bar "$MODEL_URL" -o "$MODEL_FILE"
  fi
else
  echo "✓  Model already downloaded: $MODEL_FILE"
fi

if [ ! -f "$MODEL_FILE" ]; then
  echo "❌ Model download failed: $MODEL_FILE"
  exit 1
fi

# ── 4. Quick transcription test ───────────────────────────────
echo ""
echo "🧪 Running transcription test..."
TEST_WAV="$WHISPER_DIR/samples/jfk.wav"
if [ ! -f "$TEST_WAV" ]; then
  # Create a 1-second silent WAV for a minimal test
  python3 -c "
import wave, struct, io
with wave.open('/tmp/whisper_test.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
    w.writeframes(b'\\x00\\x00' * 16000)
print('Created test WAV')
"
  TEST_WAV="/tmp/whisper_test.wav"
fi

if "$BINARY" -m "$MODEL_FILE" -f "$TEST_WAV" -nt -t 2 2>/dev/null; then
  echo "✅ Whisper.cpp transcription test passed!"
else
  echo "⚠️  Transcription test returned non-zero (may be normal for silent audio)"
fi

# ── 5. Update backend/.env ────────────────────────────────────
ENV_FILE="$BACKEND_DIR/.env"

if [ -f "$ENV_FILE" ]; then
  # Update WHISPER paths in-place
  if grep -q "WHISPER_BINARY_PATH" "$ENV_FILE"; then
    sed -i '' "s|WHISPER_BINARY_PATH=.*|WHISPER_BINARY_PATH=$BINARY|" "$ENV_FILE"
    sed -i '' "s|WHISPER_MODEL_PATH=.*|WHISPER_MODEL_PATH=$MODEL_FILE|" "$ENV_FILE"
    echo ""
    echo "✅ Updated backend/.env with Whisper paths:"
  else
    echo "" >> "$ENV_FILE"
    echo "WHISPER_BINARY_PATH=$BINARY" >> "$ENV_FILE"
    echo "WHISPER_MODEL_PATH=$MODEL_FILE" >> "$ENV_FILE"
    echo "✅ Added Whisper paths to backend/.env:"
  fi
  echo "   WHISPER_BINARY_PATH=$BINARY"
  echo "   WHISPER_MODEL_PATH=$MODEL_FILE"
else
  echo ""
  echo "⚠️  backend/.env not found. Manually add:"
  echo "   WHISPER_BINARY_PATH=$BINARY"
  echo "   WHISPER_MODEL_PATH=$MODEL_FILE"
fi

echo ""
echo "🎙️  Whisper.cpp setup complete!"
echo "   Restart the backend server to activate voice transcription."
