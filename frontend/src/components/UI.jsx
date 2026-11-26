import React from 'react';

export function Badge({ label, color = 'gray' }) {
  const colors = {
    HOT: 'bg-red-100 text-red-700 border border-red-200',
    WARM: 'bg-amber-100 text-amber-700 border border-amber-200',
    COLD: 'bg-blue-100 text-blue-700 border border-blue-200',
    CONVERTED: 'bg-green-100 text-green-700 border border-green-200',
    LOST: 'bg-gray-100 text-gray-700 border border-gray-200',
    POSITIVE: 'bg-green-100 text-green-700',
    NEUTRAL: 'bg-gray-100 text-gray-700',
    NEGATIVE: 'bg-red-100 text-red-700',
    scheduled: 'bg-indigo-100 text-indigo-700',
    completed: 'bg-green-100 text-green-700',
    cancelled: 'bg-gray-100 text-gray-500 line-through',
    active: 'bg-blue-100 text-blue-700',
    gray: 'bg-gray-100 text-gray-700',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${colors[label] || colors[color]}`}>
      {label}
    </span>
  );
}

export function ScoreBar({ score }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-blue-400';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-600">{Math.round(pct)}</span>
    </div>
  );
}

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({ title, value, subtitle, icon: Icon, color = 'indigo' }) {
  const colors = {
    indigo: 'from-indigo-500 to-indigo-600',
    green: 'from-green-500 to-emerald-600',
    amber: 'from-amber-500 to-orange-500',
    red: 'from-red-500 to-rose-600',
    purple: 'from-purple-500 to-violet-600',
    blue: 'from-blue-500 to-cyan-500',
  };
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center shadow-lg`}>
          <Icon size={22} className="text-white" />
        </div>
      </div>
    </Card>
  );
}

export function LoadingSpinner({ size = 'md' }) {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return (
    <div className={`${sizes[size]} animate-spin rounded-full border-2 border-gray-200 border-t-indigo-600`} />
  );
}

export function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        <Icon size={28} className="text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-700">{title}</h3>
      <p className="text-sm text-gray-400 mt-1 max-w-xs">{description}</p>
    </div>
  );
}
