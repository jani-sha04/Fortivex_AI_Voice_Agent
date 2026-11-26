import { useState, useRef, useCallback } from 'react';
import { voiceAPI } from '../services/api';

/**
 * useVoiceRecorder
 *
 * BUG FIXES:
 *  - Checks is_demo from /transcribe response — does NOT send empty/demo text to AI
 *  - Shows a clear user-visible message when whisper is not installed
 *  - Properly stops all media tracks on completion
 */
export function useVoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/ogg';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.start(100); // collect in 100ms chunks
      setIsRecording(true);
    } catch (err) {
      setError('Microphone access denied. Please allow microphone access in your browser.');
    }
  }, []);

  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) {
        resolve({ transcription: '', success: false, isDemo: false });
        return;
      }

      mediaRecorderRef.current.onstop = async () => {
        const mimeType = mediaRecorderRef.current?.mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: mimeType });

        // Stop all microphone tracks
        mediaRecorderRef.current?.stream?.getTracks().forEach((t) => t.stop());

        if (blob.size < 500) {
          setError('Recording too short. Please hold the button and speak clearly.');
          resolve({ transcription: '', success: false, isDemo: false });
          return;
        }

        setIsTranscribing(true);
        try {
          const response = await voiceAPI.transcribe(blob);
          const { transcription, success, is_demo, message } = response.data;

          if (is_demo) {
            // Whisper not installed — show clear message, return null transcription
            setError(
              message ||
              'Voice transcription requires whisper.cpp. Run scripts/setup_whisper.sh, ' +
              'or type your message in the text box below.'
            );
            resolve({ transcription: null, success: false, isDemo: true });
          } else if (!success || !transcription?.trim()) {
            setError('Could not transcribe audio. Please speak clearly and try again.');
            resolve({ transcription: '', success: false, isDemo: false });
          } else {
            resolve({ transcription, success: true, isDemo: false });
          }
        } catch (err) {
          setError('Transcription request failed: ' + err.message);
          resolve({ transcription: '', success: false, isDemo: false });
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorderRef.current.stop();
      setIsRecording(false);
    });
  }, []);

  return { isRecording, isTranscribing, error, startRecording, stopRecording };
}

/**
 * useAudioPlayer
 *
 * BUG FIXES:
 *  - Checks X-Demo-Mode header — if Piper not installed, skips playback silently
 *  - Properly revokes object URLs to avoid memory leaks
 */
export function useAudioPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const playAudio = useCallback(async (text) => {
    if (!text?.trim()) return;

    try {
      const response = await voiceAPI.speak(text);

      // Check if this is a demo (silent) response
      const isDemoMode = response.headers?.['x-demo-mode'] === 'true';
      if (isDemoMode) {
        // Piper not installed — skip playback silently (no error shown)
        return;
      }

      const audioBlob = new Blob([response.data], { type: 'audio/wav' });

      // Revoke previous URL
      if (audioRef.current) {
        audioRef.current.pause();
        if (audioRef.current._objectUrl) {
          URL.revokeObjectURL(audioRef.current._objectUrl);
        }
      }

      const url = URL.createObjectURL(audioBlob);
      const audio = new Audio(url);
      audio._objectUrl = url;
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(url);
      };
      audio.onerror = (e) => {
        console.warn('Audio playback error:', e);
        setIsPlaying(false);
      };

      setIsPlaying(true);
      await audio.play();
    } catch (err) {
      console.error('TTS error:', err);
      setIsPlaying(false);
      // Don't surface TTS errors to the user — TTS is optional
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  return { isPlaying, playAudio, stopAudio };
}
