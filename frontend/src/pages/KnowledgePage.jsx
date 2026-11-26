import React, { useState, useEffect, useRef } from 'react';
import { Upload, Trash2, FileText, CheckCircle, AlertCircle, Loader2, BookOpen } from 'lucide-react';
import { knowledgeAPI } from '../services/api';
import { Card, Badge, LoadingSpinner, EmptyState } from '../components/UI';

function DocCard({ doc, onDelete }) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Delete "${doc.original_name}"?`)) return;
    setDeleting(true);
    try {
      await knowledgeAPI.delete(doc.id);
      onDelete(doc.id);
    } catch (e) {
      alert(e.message);
      setDeleting(false);
    }
  };

  const statusIcons = {
    ready: <CheckCircle size={14} className="text-green-500" />,
    processing: <Loader2 size={14} className="text-blue-500 animate-spin" />,
    error: <AlertCircle size={14} className="text-red-500" />,
  };

  return (
    <div className="flex items-center gap-4 p-4 border border-gray-100 rounded-xl hover:border-indigo-200 hover:bg-indigo-50/30 transition-all group">
      <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
        <FileText size={18} className="text-indigo-600" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-800 truncate">{doc.original_name}</p>
        <p className="text-xs text-gray-400">
          {doc.file_type?.toUpperCase()} · {doc.chunk_count} chunks ·
          {doc.file_size ? ` ${(doc.file_size / 1024).toFixed(1)}KB` : ''}
        </p>
      </div>
      <div className="flex items-center gap-2">
        {statusIcons[doc.status] || null}
        <span className="text-xs capitalize text-gray-500">{doc.status}</span>
        {doc.error_message && (
          <span className="text-xs text-red-500 max-w-xs truncate" title={doc.error_message}>
            {doc.error_message}
          </span>
        )}
      </div>
      <button
        onClick={handleDelete}
        disabled={deleting}
        className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-50"
      >
        {deleting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
      </button>
    </div>
  );
}

export default function KnowledgePage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileRef = useRef(null);

  const load = async () => {
    try {
      const res = await knowledgeAPI.list();
      setDocs(res.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const uploadFile = async (file) => {
    setError(null);
    setSuccess(null);

    if (!['application/pdf', 'text/plain'].includes(file.type) &&
        !file.name.endsWith('.pdf') && !file.name.endsWith('.txt')) {
      setError('Only PDF and TXT files are supported.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File must be under 10MB.');
      return;
    }

    setUploading(true);
    try {
      await knowledgeAPI.upload(file);
      setSuccess(`"${file.name}" uploaded successfully. Processing...`);
      setTimeout(load, 2000); // Reload to show processing status
      setTimeout(load, 6000); // Reload again after processing
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  };

  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = '';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload PDF and TXT documents. The AI will use them to answer customer questions accurately.
        </p>
      </div>

      {/* Upload Area */}
      <Card
        className={`p-8 border-2 border-dashed transition-all cursor-pointer ${
          dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
      >
        <div className="flex flex-col items-center gap-3 text-center">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${
            uploading ? 'bg-indigo-100' : 'bg-gray-100'
          }`}>
            {uploading
              ? <Loader2 size={24} className="text-indigo-600 animate-spin" />
              : <Upload size={24} className="text-gray-500" />
            }
          </div>
          <div>
            <p className="text-base font-semibold text-gray-700">
              {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
            </p>
            <p className="text-sm text-gray-400 mt-1">PDF and TXT files · Max 10MB each</p>
          </div>
        </div>
        <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden" onChange={handleFileInput} />
      </Card>

      {/* Messages */}
      {error && (
        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-xl border border-red-100">
          <AlertCircle size={16} /> {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-4 py-3 rounded-xl border border-green-100">
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* Documents List */}
      <Card className="p-6">
        <h3 className="text-base font-semibold text-gray-800 mb-4">
          Uploaded Documents ({docs.length})
        </h3>
        {loading ? (
          <div className="flex justify-center py-8"><LoadingSpinner /></div>
        ) : docs.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No documents yet"
            description="Upload company documents, product catalogues, or FAQs to enable RAG-powered answers."
          />
        ) : (
          <div className="space-y-3">
            {docs.map((doc) => (
              <DocCard
                key={doc.id}
                doc={doc}
                onDelete={(id) => setDocs((prev) => prev.filter((d) => d.id !== id))}
              />
            ))}
          </div>
        )}
      </Card>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-800">
        <strong>💡 How it works:</strong> Documents are split into chunks, embedded with Sentence Transformers (all-MiniLM-L6-v2),
        and stored in ChromaDB locally. When customers ask questions, relevant chunks are retrieved and sent to Gemini for grounded answers.
        Source documents are cited in AI responses.
      </div>
    </div>
  );
}
