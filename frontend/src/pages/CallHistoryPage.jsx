import React, { useState, useEffect } from 'react';
import { History, ChevronDown, ChevronRight, User, Bot, Target, TrendingUp } from 'lucide-react';
import { conversationsAPI } from '../services/api';
import { Card, Badge, ScoreBar, LoadingSpinner, EmptyState } from '../components/UI';

function ConversationCard({ conv }) {
  const [expanded, setExpanded] = useState(false);
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  const loadSummary = async () => {
    if (summary) return;
    setLoadingSummary(true);
    try {
      const res = await conversationsAPI.getSummary(conv.id);
      setSummary(res.data);
    } catch (e) {
      setSummary({ error: 'No summary available yet' });
    } finally {
      setLoadingSummary(false);
    }
  };

  const toggleExpand = () => {
    setExpanded(!expanded);
    if (!expanded) loadSummary();
  };

  return (
    <Card className="overflow-hidden">
      <div
        className="flex items-center gap-4 p-5 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={toggleExpand}
      >
        <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center flex-shrink-0">
          <User size={18} className="text-indigo-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-800">
            {conv.customer_name || 'Anonymous Customer'}
          </p>
          <p className="text-xs text-gray-400">
            {conv.customer_email || 'No email'} ·{' '}
            {new Date(conv.created_at).toLocaleString()} ·{' '}
            {conv.messages?.length || 0} messages
          </p>
        </div>
        <div className="flex items-center gap-3">
          {conv.sentiment && <Badge label={conv.sentiment} />}
          <Badge label={conv.status} />
          {conv.lead_score > 0 && (
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Target size={12} />
              <span>{Math.round(conv.lead_score)}</span>
            </div>
          )}
          {expanded ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-100">
          {/* Messages */}
          <div className="p-5 max-h-64 overflow-y-auto space-y-3 bg-gray-50/50">
            {(conv.messages || []).map((msg) => (
              <div key={msg.id} className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === 'user' ? 'bg-indigo-600' : 'bg-purple-600'
                }`}>
                  {msg.role === 'user' ? <User size={10} className="text-white" /> : <Bot size={10} className="text-white" />}
                </div>
                <div className={`max-w-[80%] text-xs px-3 py-2 rounded-xl ${
                  msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-white border border-gray-100 text-gray-700'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="p-5 border-t border-gray-100">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">📋 Call Summary</h4>
            {loadingSummary ? (
              <LoadingSpinner size="sm" />
            ) : summary?.error ? (
              <p className="text-xs text-gray-400">{summary.error}</p>
            ) : summary ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="font-semibold text-gray-600 mb-1">Summary</p>
                  <p className="text-gray-700">{summary.full_summary}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="font-semibold text-gray-600 mb-1">Requirements</p>
                  <p className="text-gray-700">{summary.requirements}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="font-semibold text-gray-600 mb-1">Products Discussed</p>
                  <p className="text-gray-700">{summary.products_discussed}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="font-semibold text-gray-600 mb-1">Recommended Action</p>
                  <p className="text-gray-700">{summary.recommended_action}</p>
                </div>
                {summary.lead_score > 0 && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="font-semibold text-gray-600 mb-2">Lead Score</p>
                    <ScoreBar score={summary.lead_score} />
                  </div>
                )}
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="font-semibold text-gray-600 mb-1">Objections</p>
                  <p className="text-gray-700">{summary.objections || 'None noted'}</p>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </Card>
  );
}

export default function CallHistoryPage() {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    conversationsAPI.list()
      .then(r => setConversations(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
        <p className="text-sm text-gray-500 mt-1">{conversations.length} conversations · Click to expand transcript and summary</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : error ? (
        <div className="p-6 bg-red-50 rounded-xl text-red-600 text-sm">{error}</div>
      ) : conversations.length === 0 ? (
        <Card>
          <EmptyState
            icon={History}
            title="No conversations yet"
            description="Start a conversation with the AI Agent to see transcripts, summaries, and sentiment analysis here."
          />
        </Card>
      ) : (
        <div className="space-y-4">
          {conversations.map((conv) => (
            <ConversationCard key={conv.id} conv={conv} />
          ))}
        </div>
      )}
    </div>
  );
}
