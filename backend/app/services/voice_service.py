"""
Voice Processing Service
Handles Whisper.cpp STT and Piper TTS.

BUG FIXES applied:
  - _demo_transcription now returns empty string + is_demo=True (not fake text)
  - Whisper uses -nt flag (no timestamps in output) for cleaner text
  - ffmpeg forced conversion to 16kHz mono WAV always (not just non-WAV)
  - PiperTTS: silent WAV placeholder clearly returns is_demo=True
  - Both services expose clear status/error messages for the frontend
"""

import os
import subprocess
import logging
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


class WhisperService:
    """
    Speech-to-Text using whisper.cpp
    Runs local inference with Apple Silicon Metal acceleration.
    """

    def __init__(self):
        self.binary = settings.WHISPER_BINARY_PATH
        self.model = settings.WHISPER_MODEL_PATH
        self._check_availability()

    def _check_availability(self):
        """Check if whisper.cpp binary and model exist and are executable."""
        binary_ok = os.path.isfile(self.binary) and os.access(self.binary, os.X_OK)
        model_ok = os.path.isfile(self.model)
        self.available = binary_ok and model_ok

        if not binary_ok:
            logger.warning(
                f"Whisper.cpp binary not found or not executable: {self.binary}\n"
                "  → Run: bash scripts/setup_whisper.sh"
            )
        elif not model_ok:
            logger.warning(
                f"Whisper model not found: {self.model}\n"
                "  → Run: bash scripts/setup_whisper.sh"
            )

    def transcribe(self, audio_path: str) -> Tuple[str, bool, bool]:
        """
        Transcribe audio file using whisper.cpp.
        Returns (transcription_text, success_bool, is_demo_bool)

        IMPORTANT: when whisper is not available, returns ("", False, True)
        so the caller knows NOT to send empty/fake text to the AI.
        """
        if not self.available:
            logger.info("Whisper not available — returning is_demo=True, no transcription")
            return "", False, True  # is_demo=True

        # Always convert to 16kHz mono WAV for whisper compatibility
        wav_path = self._to_wav(audio_path)
        if not wav_path:
            return "", False, False

        try:
            cmd = [
                self.binary,
                "-m", self.model,
                "-f", wav_path,
                "--output-txt",   # write text to <input>.txt
                "-nt",            # no timestamps in output
                "-t", "4",        # 4 threads (safe for M4)
                "-l", "auto",     # auto-detect language
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                logger.error(f"Whisper stderr: {result.stderr}")
                return "", False, False

            # Whisper with --output-txt writes to <input_file>.txt
            txt_path = wav_path + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path, "r") as f:
                    text = f.read().strip()
                os.remove(txt_path)
            else:
                # Fallback: parse stdout
                text = result.stdout.strip()

            # Clean up whisper's bracket annotations
            import re
            text = re.sub(r"\[.*?\]", "", text).strip()

            if not text:
                logger.warning("Whisper returned empty transcription")
                return "", False, False

            logger.info(f"Transcribed: '{text[:80]}...'")
            return text, True, False

        except subprocess.TimeoutExpired:
            logger.error("Whisper transcription timed out (>120s)")
            return "", False, False
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return "", False, False
        finally:
            # Clean up converted WAV
            if wav_path != audio_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    def _to_wav(self, audio_path: str) -> Optional[str]:
        """
        Convert any audio to 16kHz mono WAV using ffmpeg.
        Always converts (even WAV input) to ensure correct sample rate/format.
        """
        wav_path = str(TEMP_DIR / f"{uuid.uuid4()}_16k.wav")
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", audio_path,
                    "-ar", "16000",   # 16 kHz sample rate (required by whisper)
                    "-ac", "1",       # mono
                    "-c:a", "pcm_s16le",
                    wav_path,
                ],
                capture_output=True,
                timeout=60,
            )
            if result.returncode == 0:
                return wav_path
            else:
                logger.error(f"ffmpeg conversion failed: {result.stderr.decode(errors='ignore')}")
                return None
        except FileNotFoundError:
            logger.error("ffmpeg not found — install with: brew install ffmpeg")
            return None
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return None


class PiperTTSService:
    """
    Text-to-Speech using Piper TTS.
    Local neural voice synthesis with ONNX models.
    """

    def __init__(self):
        self.binary = settings.PIPER_BINARY_PATH
        self.model = settings.PIPER_MODEL_PATH
        self._check_availability()

    def _check_availability(self):
        """Check if Piper binary and model exist."""
        binary_ok = os.path.isfile(self.binary) and os.access(self.binary, os.X_OK)
        model_ok = os.path.isfile(self.model)
        self.available = binary_ok and model_ok

        if not binary_ok:
            logger.warning(
                f"Piper TTS binary not found or not executable: {self.binary}\n"
                "  → Run: bash scripts/setup_piper.sh"
            )
        elif not model_ok:
            logger.warning(
                f"Piper voice model not found: {self.model}\n"
                "  → Run: bash scripts/setup_piper.sh"
            )

    def synthesize(self, text: str) -> Tuple[Optional[bytes], bool, bool]:
        """
        Synthesize speech from text.
        Returns (audio_bytes_or_None, success_bool, is_demo_bool)
        """
        if not self.available:
            # Return a silent WAV so the frontend doesn't error — clearly marked is_demo
            return self._silent_wav(), True, True

        output_path = str(TEMP_DIR / f"{uuid.uuid4()}.wav")

        try:
            # Piper reads from stdin
            result = subprocess.run(
                [
                    self.binary,
                    "--model", self.model,
                    "--output_file", output_path,
                ],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=90,
            )

            if result.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size < 100:
                    logger.error(f"Piper output file too small: {file_size} bytes")
                    return None, False, False
                with open(output_path, "rb") as f:
                    audio_data = f.read()
                logger.info(f"Piper synthesized {len(audio_data)} bytes for '{text[:40]}...'")
                return audio_data, True, False
            else:
                logger.error(f"Piper error (rc={result.returncode}): {result.stderr.decode(errors='ignore')}")
                return None, False, False

        except subprocess.TimeoutExpired:
            logger.error("Piper TTS timed out")
            return None, False, False
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            return None, False, False
        finally:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass

    def _silent_wav(self) -> bytes:
        """Return a minimal valid silent WAV (0.5 second) as placeholder."""
        import io
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(22050)
            silence = b"\x00\x00" * 11025  # 0.5 second silence
            wav.writeframes(silence)
        return buffer.getvalue()


# Singletons
whisper_service = WhisperService()
piper_service = PiperTTSService()
