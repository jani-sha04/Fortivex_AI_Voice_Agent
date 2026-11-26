import React, { useState, useEffect } from 'react';
import { Settings, Mic2, Brain, Building2, AlertCircle, CheckCircle } from 'lucide-react';
import { agentAPI, voiceAPI } from '../services/api';
import { Card } from '../components/UI';

function SettingRow({ label, value, description }) {
  return (
    <div className="flex items-start justify-between py-3 border-b border-gray-100 last:border-0">
      <div>
        <p className="text-sm font-medium text-gray-800">{label}</p>
        {description && <p className="text-xs text-gray-400 mt-0.5">{description}</p>}
      </div>
      <div className="ml-4 text-right">
        <span className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-700">
          {value || '—'}
        </span>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [agentStatus, setAgentStatus] = useState(null);
  const [voiceStatus, setVoiceStatus] = useState(null);

  useEffect(() => {
    agentAPI.status().then(r => setAgentStatus(r.data)).catch(() => {});
    voiceAPI.status().then(r => setVoiceStatus(r.data)).catch(() => {});
  }, []);

  const StatusIndicator = ({ available, label }) => (
    <div className={`flex items-center gap-2 text-sm ${available ? 'text-green-600' : 'text-amber-600'}`}>
      {available
        ? <CheckCircle size={14} />
        : <AlertCircle size={14} />
      }
      {available ? `${label} Connected` : `${label} Not Configured`}
    </div>
  );

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Application configuration and integration status</p>
      </div>

      {/* AI Configuration */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center">
            <Brain size={16} className="text-indigo-600" />
          </div>
          <h2 className="text-base font-semibold text-gray-800">AI Configuration</h2>
        </div>

        {agentStatus && (
          <div className="mb-4">
            <StatusIndicator available={!agentStatus.demo_mode} label="Gemini API" />
          </div>
        )}

        <div className="space-y-1">
          <SettingRow
            label="AI Model"
            value="gemini-1.5-flash"
            description="Set via GEMINI_MODEL in .env file"
          />
          <SettingRow
            label="Demo Mode"
            value={agentStatus?.demo_mode ? 'ENABLED' : 'DISABLED'}
            description="Demo mode is active when GEMINI_API_KEY is not set"
          />
          <SettingRow
            label="API Key"
            value="Set via GEMINI_API_KEY in .env"
            description="Never expose API keys in the browser or frontend code"
          />
        </div>

        <div className="mt-4 bg-amber-50 border border-amber-100 rounded-lg p-3 text-sm text-amber-800">
          <strong>⚙️ To configure Gemini:</strong> Copy <code>.env.example</code> to <code>.env</code> in the backend directory and set your <code>GEMINI_API_KEY</code>.
          Get a free key at <a href="https://aistudio.google.com" target="_blank" rel="noopener noreferrer" className="underline">aistudio.google.com</a>
        </div>
      </Card>

      {/* Voice Configuration */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
            <Mic2 size={16} className="text-purple-600" />
          </div>
          <h2 className="text-base font-semibold text-gray-800">Voice Processing</h2>
        </div>

        {voiceStatus && (
          <div className="mb-4 space-y-1">
            <StatusIndicator available={voiceStatus.whisper_available} label="Whisper.cpp (STT)" />
            <StatusIndicator available={voiceStatus.piper_available} label="Piper TTS" />
          </div>
        )}

        <div className="space-y-1">
          <SettingRow
            label="Speech-to-Text"
            value="whisper.cpp (local)"
            description="Apple Silicon Metal acceleration · base.en model"
          />
          <SettingRow
            label="Text-to-Speech"
            value="Piper TTS (local)"
            description="ONNX neural voice · en_US-lessac-medium"
          />
          <SettingRow
            label="Audio Format"
            value="WAV 16kHz mono"
            description="Whisper.cpp input requirement"
          />
        </div>

        <div className="mt-4 bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-800">
          <strong>⚙️ To set up voice:</strong> Run <code>./scripts/setup_whisper.sh</code> and <code>./scripts/setup_piper.sh</code> from the project root.
          These install whisper.cpp (with Metal support) and Piper TTS locally.
        </div>
      </Card>

      {/* Company Configuration */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
            <Building2 size={16} className="text-green-600" />
          </div>
          <h2 className="text-base font-semibold text-gray-800">Demo Company Configuration</h2>
        </div>

        <div className="space-y-1">
          <SettingRow label="Company Name" value="NovaTech Solutions" description="Set via COMPANY_NAME in .env" />
          <SettingRow label="Industry" value="Enterprise Software" description="Set via COMPANY_INDUSTRY in .env" />
          <SettingRow label="Agent Name" value="Shara" description="Set via AGENT_NAME in .env" />
        </div>

        <div className="mt-4 bg-green-50 border border-green-100 rounded-lg p-3 text-sm text-green-800">
          <strong>📌 Note:</strong> This is a demonstration company. Update <code>COMPANY_NAME</code>, <code>COMPANY_INDUSTRY</code>,
          and <code>AGENT_NAME</code> in your <code>.env</code> file to customize the agent identity.
          Upload your own documents to the Knowledge Base for company-specific answers.
        </div>
      </Card>

      {/* System Info */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
            <Settings size={16} className="text-gray-600" />
          </div>
          <h2 className="text-base font-semibold text-gray-800">System Information</h2>
        </div>
        <div className="space-y-1">
          <SettingRow label="Backend" value="FastAPI + Uvicorn" description="Python 3.12 · Port 8000" />
          <SettingRow label="Database" value="SQLite (local)" description="Production: migrate to PostgreSQL" />
          <SettingRow label="Vector Store" value="ChromaDB (local)" description="Sentence Transformers all-MiniLM-L6-v2" />
          <SettingRow label="Frontend" value="React + Vite + Tailwind" description="Port 5173" />
          <SettingRow label="API Docs" value="/docs (Swagger)" description="FastAPI auto-generated OpenAPI documentation" />
        </div>
      </Card>
    </div>
  );
}
