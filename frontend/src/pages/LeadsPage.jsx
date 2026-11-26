import React, { useState, useEffect } from 'react';
import { Search, Filter, Users, ChevronDown, Mail, Phone, Building2, ExternalLink } from 'lucide-react';
import { leadsAPI } from '../services/api';
import { Card, Badge, ScoreBar, LoadingSpinner, EmptyState } from '../components/UI';

function LeadRow({ lead, onClick }) {
  return (
    <tr
      className="hover:bg-gray-50 cursor-pointer transition-colors"
      onClick={() => onClick(lead)}
    >
      <td className="px-6 py-4">
        <div className="font-medium text-gray-900">{lead.name || '—'}</div>
        <div className="text-xs text-gray-400">{lead.email || '—'}</div>
      </td>
      <td className="px-6 py-4 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <Building2 size={12} className="text-gray-400" />
          {lead.company || '—'}
        </div>
      </td>
      <td className="px-6 py-4 text-sm text-gray-600">{lead.industry || '—'}</td>
      <td className="px-6 py-4 text-sm text-gray-600">{lead.product_interest || '—'}</td>
      <td className="px-6 py-4 w-32">
        <ScoreBar score={lead.lead_score} />
      </td>
      <td className="px-6 py-4">
        <Badge label={lead.status || 'COLD'} />
      </td>
      <td className="px-6 py-4">
        {lead.sentiment && <Badge label={lead.sentiment} />}
      </td>
    </tr>
  );
}

function LeadModal({ lead, onClose, onUpdate }) {
  const [status, setStatus] = useState(lead.status);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await leadsAPI.update(lead.id, { status });
      onUpdate();
      onClose();
    } catch (e) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-100 flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{lead.name || 'Unknown Customer'}</h2>
            <p className="text-sm text-gray-500">{lead.company} · {lead.industry}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {[
              ['Email', lead.email, Mail],
              ['Phone', lead.phone, Phone],
              ['Budget', lead.budget, null],
              ['Timeline', lead.timeline, null],
              ['Intent', lead.intent, null],
            ].map(([label, value, Icon]) => (
              <div key={label} className="bg-gray-50 rounded-xl p-3">
                <p className="text-xs font-medium text-gray-500 mb-1">{label}</p>
                <p className="text-sm font-medium text-gray-800">{value || '—'}</p>
              </div>
            ))}
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-xs font-medium text-gray-500 mb-1">Lead Score</p>
              <ScoreBar score={lead.lead_score} />
            </div>
          </div>

          {lead.requirements && (
            <div className="bg-indigo-50 rounded-xl p-4">
              <p className="text-xs font-semibold text-indigo-700 mb-1">Requirements</p>
              <p className="text-sm text-gray-700">{lead.requirements}</p>
            </div>
          )}

          {lead.notes && (
            <div className="bg-amber-50 rounded-xl p-4">
              <p className="text-xs font-semibold text-amber-700 mb-1">Notes / Scoring Reason</p>
              <p className="text-sm text-gray-700">{lead.notes}</p>
            </div>
          )}

          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Status:</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="px-3 py-1.5 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
            >
              {['HOT', 'WARM', 'COLD', 'CONVERTED', 'LOST'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              onClick={save}
              disabled={saving}
              className="px-4 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Update'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LeadsPage() {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedLead, setSelectedLead] = useState(null);

  const load = async () => {
    try {
      const res = await leadsAPI.list({ search, status: statusFilter || undefined });
      setLeads(res.data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Lead Management</h1>
          <p className="text-sm text-gray-500 mt-1">{leads.length} leads total</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search leads..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 rounded-lg border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
        >
          <option value="">All Statuses</option>
          {['HOT', 'WARM', 'COLD', 'CONVERTED', 'LOST'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <Card>
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
        ) : error ? (
          <div className="p-6 text-red-600 text-sm">{error}</div>
        ) : leads.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No leads yet"
            description="Start a conversation with the AI Agent to generate leads automatically."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Customer', 'Company', 'Industry', 'Interest', 'Score', 'Status', 'Sentiment'].map((h) => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {leads.map((lead) => (
                  <LeadRow key={lead.id} lead={lead} onClick={setSelectedLead} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selectedLead && (
        <LeadModal lead={selectedLead} onClose={() => setSelectedLead(null)} onUpdate={load} />
      )}
    </div>
  );
}
