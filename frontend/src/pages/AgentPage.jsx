import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic, MicOff, Send, Volume2, VolumeX, Bot, User,
  Loader2, AlertCircle, CheckCircle, RefreshCw, Zap,
} from 'lucide-react';
import { agentAPI, conversationsAPI } from '../services/api';
import { useVoiceRecorder, useAudioPlayer } from '../hooks/useVoice';
import { Card, Badge } from '../components/UI';

// ── Message bubble component ───────────────────────────────────────────────
function Message({ msg }) {
  const isUser = msg.role === 'user';
  const isError = msg.isError;

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser
            ? 'bg-indigo-600'
            : isError
              ? 'bg-red-100'
              : 'bg-gradient-to-br from-purple-500 to-indigo-600'
        }`}
      >
        {isUser ? (
          <User size={14} className="text-white" />
        ) : (
          <Bot size={14} className={isError ? 'text-red-500' : 'text-white'} />
        )}
      </div>

      <div
        className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
          isUser
            ? 'bg-indigo-600 text-white rounded-tr-sm'
            : isError
              ? 'bg-red-50 text-red-700 border border-red-200 rounded-tl-sm'
              : 'bg-white text-gray-800 border border-gray-100 rounded-tl-sm'
        }`}
      >
        {/* Only show demo badge — NEVER show [DEMO MODE] inline in content */}
        {msg.isDemo && !isUser && (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full mb-2 mr-2">
            ⚠️ Demo Mode
          </span>
        )}
        {msg.isVoice && (
          <span className="inline-flex items-center gap-1 text-xs text-indigo-500 mb-1 mr-2">
            🎙️ Voice
          </span>
        )}

        <span>{msg.content}</span>

        {/* Tool calls badge */}
        {msg.toolCalls && msg.toolCalls.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {msg.toolCalls.map((t, i) => (
              <span
                key={i}
                className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full inline-flex items-center gap-1"
              >
                <Zap size={10} /> {t}
              </span>
            ))}
          </div>
        )}

        {/* RAG sources */}
        {msg.ragSources && msg.ragSources.length > 0 && (
          <div className="mt-1 text-xs opacity-50">
            📚 {msg.ragSources.join(', ')}
          </div>
        )}

        {/* Timestamp */}
        {msg.timestamp && (
          <div className="mt-1 text-xs opacity-40 text-right">
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Typing indicator ────────────────────────────────────────────────────────
function TypingIndicator({ label = 'Shara is thinking...' }) {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
        <Bot size={14} className="text-white" />
      </div>
      <div className="bg-white border border-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
          </div>
          <span className="text-xs text-gray-400">{label}</span>
        </div>
      </div>
    </div>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────
export default function AgentPage() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hello! I'm Shara, your AI Sales Executive at NovaTech Solutions. How can I help you today? " +
        "I can answer questions about our products, understand your requirements, or schedule a demo.",
      isDemo: false,
      timestamp: new Date().toISOString(),
    },
  ]);

  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [conversationId, setConversationId] = useState(null);
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [agentStatus, setAgentStatus] = useState(null);
  const [statusError, setStatusError] = useState(null);

  const messagesEndRef = useRef(null);

  const {
    isRecording, isTranscribing,
    error: voiceError,
    startRecording, stopRecording,
  } = useVoiceRecorder();

  const { isPlaying, playAudio, stopAudio } = useAudioPlayer();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load agent status on mount
  useEffect(() => {
    agentAPI.status()
      .then((r) => setAgentStatus(r.data))
      .catch(() => setStatusError('Could not reach backend'));
  }, []);

  // ── Send a text message ──────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (text, isVoice = false) => {
      if (!text?.trim() || isSending) return;

      const userMsg = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: text.trim(),
        isVoice,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setIsSending(true);

      try {
        const res = await agentAPI.chat(text.trim(), sessionId, conversationId);
        const { response, conversation_id, is_demo, tool_calls, rag_sources } = res.data;

        if (!conversationId && conversation_id) setConversationId(conversation_id);

        const aiMsg = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: response,
          isDemo: Boolean(is_demo),
          toolCalls: tool_calls || [],
          ragSources: rag_sources || [],
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, aiMsg]);

        // Auto-speak response if TTS enabled
        if (autoSpeak && response && !is_demo) {
          setIsSpeaking(true);
          await playAudio(response).finally(() => setIsSpeaking(false));
        }
      } catch (e) {
        const errorMsg = e.message || 'Unknown error';
        setMessages((prev) => [
          ...prev,
          {
            id: `err-${Date.now()}`,
            role: 'assistant',
            content: `⚠️ Error: ${errorMsg}. Please check that the backend is running on port 8000.`,
            isError: true,
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setIsSending(false);
      }
    },
    [isSending, sessionId, conversationId, autoSpeak, playAudio]
  );

  // ── Voice toggle ─────────────────────────────────────────────────────────
  const handleVoiceToggle = async () => {
    if (isRecording) {
      const result = await stopRecording();
      // Only send if we got a real transcription (not demo/empty)
      if (result?.transcription && result.transcription.trim()) {
        await sendMessage(result.transcription, true);
      }
      // If result.isDemo, the useVoice hook already set a voiceError message
    } else {
      await startRecording();
    }
  };

  // ── New conversation ─────────────────────────────────────────────────────
  const startNewConversation = () => {
    // Reset conversation state — session ID stays (new session created by backend)
    setConversationId(null);
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content:
          "Starting a fresh conversation. I'm Shara — how can I help you today?",
        isDemo: false,
        timestamp: new Date().toISOString(),
      },
    ]);
  };

  // ── End & summarize ─────────────────────────────────────────────────────
  const endConversation = async () => {
    if (!conversationId) return;
    try {
      await conversationsAPI.end(conversationId);
      setMessages((prev) => [
        ...prev,
        {
          id: `end-${Date.now()}`,
          role: 'assistant',
          content: '✅ Conversation ended and summary generated. You can view it in Call History.',
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (e) {
      console.error('End conversation error:', e);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] max-h-[900px]">
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Voice Agent</h1>
          <p className="text-sm text-gray-500">Talk to Shara — your AI Sales Executive</p>
        </div>

        <div className="flex items-center gap-2">
          {/* Gemini status pill */}
          {agentStatus && (
            <div
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full font-medium ${
                agentStatus.demo_mode
                  ? 'bg-amber-100 text-amber-700 border border-amber-200'
                  : 'bg-green-100 text-green-700 border border-green-200'
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full animate-pulse ${
                  agentStatus.demo_mode ? 'bg-amber-500' : 'bg-green-500'
                }`}
              />
              {agentStatus.demo_mode ? '⚠️ Demo Mode (no API key)' : '✓ Gemini Connected'}
            </div>
          )}
          {statusError && (
            <div className="flex items-center gap-1 text-xs text-red-600 bg-red-50 px-3 py-1.5 rounded-full border border-red-200">
              <AlertCircle size={12} /> Backend offline
            </div>
          )}

          {/* Voice pipeline status */}
          {agentStatus && (
            <div
              className={`flex items-center gap-1.5 text-xs px-2 py-1.5 rounded-full ${
                agentStatus.voice_pipeline_ready
                  ? 'bg-indigo-50 text-indigo-600'
                  : 'bg-gray-100 text-gray-400'
              }`}
              title={agentStatus.voice_pipeline_ready ? 'Voice pipeline ready' : 'Voice not configured — run setup_whisper.sh & setup_piper.sh'}
            >
              {agentStatus.voice_pipeline_ready ? '🎙️ Voice Ready' : '🎙️ Voice Off'}
            </div>
          )}

          {/* Auto-speak toggle */}
          <button
            onClick={() => setAutoSpeak(!autoSpeak)}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-colors ${
              autoSpeak
                ? 'bg-indigo-50 border-indigo-200 text-indigo-700'
                : 'border-gray-200 text-gray-500 hover:border-gray-300'
            }`}
          >
            {autoSpeak ? <Volume2 size={12} /> : <VolumeX size={12} />}
            Auto-speak
          </button>

          {/* New conversation */}
          <button
            onClick={startNewConversation}
            className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-500 hover:bg-gray-50"
            title="Start a new conversation"
          >
            <RefreshCw size={12} /> New Chat
          </button>

          {/* End & summarize */}
          {conversationId && (
            <button
              onClick={endConversation}
              className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-500 hover:bg-gray-50"
            >
              End & Summarize
            </button>
          )}
        </div>
      </div>

      {/* ── Demo Mode Banner ── */}
      {agentStatus?.demo_mode && (
        <div className="mb-3 flex items-start gap-2 text-xs bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-xl">
          <AlertCircle size={14} className="mt-0.5 flex-shrink-0" />
          <div>
            <strong>Demo Mode Active</strong> — Gemini API key not configured.
            Responses are pre-scripted and not AI-generated.{' '}
            <span className="font-mono bg-amber-100 px-1 rounded">
              Set GEMINI_API_KEY in backend/.env
            </span>{' '}
            and restart the backend to enable real AI.
          </div>
        </div>
      )}

      {/* ── Session info ── */}
      {conversationId && (
        <div className="text-xs text-gray-400 mb-2 flex items-center gap-2">
          <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
            Session: {sessionId.slice(0, 8)}…
          </span>
          <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">
            Conv: {conversationId.slice(0, 8)}…
          </span>
        </div>
      )}

      {/* ── Messages ── */}
      <Card className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg) => (
          <Message key={msg.id} msg={msg} />
        ))}

        {/* Typing / transcribing indicator */}
        {isSending && <TypingIndicator label="Shara is thinking..." />}
        {isTranscribing && <TypingIndicator label="Transcribing your voice..." />}

        {/* Speaking indicator */}
        {isSpeaking && (
          <div className="text-center text-xs text-indigo-600 animate-pulse">
            🔊 Shara is speaking…
          </div>
        )}
        {isPlaying && (
          <div className="text-center text-xs text-indigo-500">
            ▶ Playing audio response
          </div>
        )}

        <div ref={messagesEndRef} />
      </Card>

      {/* ── Voice error banner ── */}
      {voiceError && (
        <div className="mt-2 flex items-start gap-2 text-sm text-orange-700 bg-orange-50 border border-orange-200 px-3 py-2 rounded-lg">
          <AlertCircle size={14} className="mt-0.5 flex-shrink-0 text-orange-500" />
          <span>{voiceError}</span>
        </div>
      )}

      {/* ── Input area ── */}
      <div className="mt-3 flex gap-2">
        {/* Mic button */}
        <button
          onClick={handleVoiceToggle}
          disabled={isTranscribing || isSending}
          className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all flex-shrink-0 ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse shadow-lg shadow-red-200'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title={isRecording ? 'Stop recording' : 'Start voice recording (requires whisper.cpp)'}
        >
          {isTranscribing ? (
            <Loader2 size={18} className="animate-spin" />
          ) : isRecording ? (
            <MicOff size={18} />
          ) : (
            <Mic size={18} />
          )}
        </button>

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isRecording
                ? '🎙️ Recording… click mic to stop and transcribe'
                : 'Type a message or use the mic…'
            }
            rows={1}
            className="w-full px-4 py-3 pr-12 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none text-sm bg-white"
            disabled={isRecording || isSending}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isSending || isRecording}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-7 h-7 rounded-lg bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-700 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {isSending ? <Loader2 size={12} className="animate-spin" /> : <Send size={13} />}
          </button>
        </div>
      </div>

      {/* ── Recording indicator ── */}
      {isRecording && (
        <div className="mt-2 text-center">
          <span className="inline-flex items-center gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-4 py-2 rounded-full">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
            Recording… Click the mic to stop and transcribe
          </span>
        </div>
      )}
    </div>
  );
}
