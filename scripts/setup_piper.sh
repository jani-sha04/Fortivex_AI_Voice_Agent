#!/usr/bin/env bash
# ============================================================
# Setup Piper TTS for FORTIVEX AI Sales Agent
# Downloads pre-built macOS ARM64 binary and voice model
# ============================================================
# Usage: bash scripts/setup_piper.sh
# ============================================================
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
PIPER_DIR="$BACKEND_DIR/piper"

mkdir -p "$PIPER_DIR"

echo ""
echo "🔊 Setting up Piper TTS for Apple Silicon M4..."
echo "   Piper dir: $PIPER_DIR"
echo ""

# ── 1. Download Piper binary ──────────────────────────────────
ARCH=$(uname -m)
PIPER_BINARY="$PIPER_DIR/piper"

if [ -f "$PIPER_BINARY" ] && [ -x "$PIPER_BINARY" ]; then
  echo "✓  Piper binary already present."
else
  echo "📥 Downloading Piper binary for $ARCH..."

  # Try multiple release versions in order
  PIPER_VERSIONS=("2023.11.14-2" "2024.02.07-1" "2023.11.14-1")
  DOWNLOAD_OK=false

  for VER in "${PIPER_VERSIONS[@]}"; do
    if [ "$ARCH" = "arm64" ]; then
      TARBALL="piper_macos_aarch64.tar.gz"
    else
      TARBALL="piper_macos_x86_64.tar.gz"
    fi

    URL="https://github.com/rhasspy/piper/releases/download/$VER/$TARBALL"
    echo "   Trying: $URL"

    if curl -fL --progress-bar "$URL" -o "$PIPER_DIR/piper_release.tar.gz" 2>/dev/null; then
      DOWNLOAD_OK=true
      echo "   ✓ Downloaded version $VER"
      break
    else
      echo "   ✗ Version $VER not found, trying next..."
    fi
  done

  if [ "$DOWNLOAD_OK" = false ]; then
    echo "❌ Failed to download Piper binary from GitHub releases."
    echo ""
    echo "   Manual installation:"
    echo "   1. Go to: https://github.com/rhasspy/piper/releases"
    echo "   2. Download piper_macos_aarch64.tar.gz"
    echo "   3. Extract the 'piper' binary to: $PIPER_DIR/piper"
    echo "   4. chmod +x $PIPER_DIR/piper"
    exit 1
  fi

  cd "$PIPER_DIR"
  tar xzf piper_release.tar.gz
  rm -f piper_release.tar.gz

  # Find the piper binary (may be nested in a subdirectory)
  FOUND_BIN=$(find "$PIPER_DIR" -name "piper" -type f ! -name "*.so" ! -name "*.dylib" 2>/dev/null | head -1)
  if [ -z "$FOUND_BIN" ]; then
    # Try executable search
    FOUND_BIN=$(find "$PIPER_DIR" -type f -perm +111 -name "piper*" 2>/dev/null | grep -v "\.so$\|\.dylib$\|\.json$" | head -1)
  fi

  if [ -n "$FOUND_BIN" ] && [ "$FOUND_BIN" != "$PIPER_BINARY" ]; then
    cp "$FOUND_BIN" "$PIPER_BINARY"
  fi

  if [ ! -f "$PIPER_BINARY" ]; then
    echo "❌ Could not locate piper binary after extraction."
    echo "   Contents of $PIPER_DIR:"
    ls -la "$PIPER_DIR"
    exit 1
  fi

  chmod +x "$PIPER_BINARY"
  echo "   Binary: $PIPER_BINARY"
fi

# ── 2. Download voice model ───────────────────────────────────
MODEL_FILE="$PIPER_DIR/en_US-lessac-medium.onnx"
CONFIG_FILE="$PIPER_DIR/en_US-lessac-medium.onnx.json"

if [ -f "$MODEL_FILE" ] && [ -f "$CONFIG_FILE" ]; then
  echo "✓  Voice model already downloaded."
else
  echo ""
  echo "📥 Downloading en_US-lessac-medium voice model (~60MB)..."
  MODEL_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
  CONFIG_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

  curl -L --progress-bar "$MODEL_URL" -o "$MODEL_FILE"
  curl -L --progress-bar "$CONFIG_URL" -o "$CONFIG_FILE"

  if [ ! -f "$MODEL_FILE" ]; then
    echo "❌ Model download failed: $MODEL_FILE"
    exit 1
  fi
  echo "   Model: $MODEL_FILE"
fi

# ── 3. Test TTS ───────────────────────────────────────────────
echo ""
echo "🧪 Testing Piper TTS..."
TEST_WAV="/tmp/piper_test_$(date +%s).wav"

echo "Hello! I am Aria, your AI sales assistant from NovaTech Solutions." \
  | "$PIPER_BINARY" \
      --model "$MODEL_FILE" \
      --output_file "$TEST_WAV" 2>/dev/null

if [ -f "$TEST_WAV" ] && [ "$(wc -c < "$TEST_WAV")" -gt 1000 ]; then
  SIZE=$(du -h "$TEST_WAV" | cut -f1)
  echo "✅ Piper TTS working! Generated $SIZE audio file."
  echo "   Test audio: $TEST_WAV"
  echo "   Play with: afplay $TEST_WAV"
  rm -f "$TEST_WAV"
else
  echo "⚠️  Piper test produced no/tiny output — check binary compatibility."
  echo "   Try: file $PIPER_BINARY"
fi

# ── 4. Update backend/.env ────────────────────────────────────
ENV_FILE="$BACKEND_DIR/.env"

if [ -f "$ENV_FILE" ]; then
  if grep -q "PIPER_BINARY_PATH" "$ENV_FILE"; then
    sed -i '' "s|PIPER_BINARY_PATH=.*|PIPER_BINARY_PATH=$PIPER_BINARY|" "$ENV_FILE"
    sed -i '' "s|PIPER_MODEL_PATH=.*|PIPER_MODEL_PATH=$MODEL_FILE|" "$ENV_FILE"
    echo ""
    echo "✅ Updated backend/.env with Piper paths:"
  else
    echo "" >> "$ENV_FILE"
    echo "PIPER_BINARY_PATH=$PIPER_BINARY" >> "$ENV_FILE"
    echo "PIPER_MODEL_PATH=$MODEL_FILE" >> "$ENV_FILE"
    echo "✅ Added Piper paths to backend/.env:"
  fi
  echo "   PIPER_BINARY_PATH=$PIPER_BINARY"
  echo "   PIPER_MODEL_PATH=$MODEL_FILE"
else
  echo ""
  echo "⚠️  backend/.env not found. Manually add:"
  echo "   PIPER_BINARY_PATH=$PIPER_BINARY"
  echo "   PIPER_MODEL_PATH=$MODEL_FILE"
fi

echo ""
echo "🔊 Piper TTS setup complete!"
echo "   Restart the backend server to activate voice responses."
