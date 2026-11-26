import React, { useState, useEffect } from 'react';
import { Users, TrendingUp, Calendar, MessageSquare, Target, Award } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { dashboardAPI } from '../services/api';
import { StatCard, Card, Badge, LoadingSpinner } from '../components/UI';

const SENTIMENT_COLORS = { POSITIVE: '#10b981', NEUTRAL: '#6366f1', NEGATIVE: '#ef4444', Unknown: '#9ca3af' };

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await dashboardAPI.analytics();
        setData(res.data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64"><LoadingSpinner size="lg" /></div>
  );

  if (error) return (
    <div className="p-6 bg-red-50 rounded-xl text-red-700 border border-red-200">
      <strong>Error loading dashboard:</strong> {error}
    </div>
  );

  const sentimentData = data
    ? Object.entries(data.sentiment_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Sales Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Real-time overview of your AI sales performance</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard title="Total Leads" value={data.total_leads} subtitle="All time" icon={Users} color="indigo" />
        <StatCard title="Hot Leads" value={data.hot_leads} subtitle="High intent" icon={Target} color="red" />
        <StatCard title="Warm Leads" value={data.warm_leads} subtitle="Nurturing" icon={TrendingUp} color="amber" />
        <StatCard title="Conversations" value={data.total_conversations} subtitle="Total sessions" icon={MessageSquare} color="blue" />
        <StatCard title="Appointments" value={data.total_appointments} subtitle="Scheduled" icon={Calendar} color="green" />
        <StatCard title="Conversion Rate" value={`${data.conversion_rate}%`} subtitle="Lead to customer" icon={Award} color="purple" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trend */}
        <Card className="p-6">
          <h3 className="text-base font-semibold text-gray-800 mb-4">Monthly Lead Trend</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.monthly_trend}>
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="leads" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Sentiment Distribution */}
        <Card className="p-6">
          <h3 className="text-base font-semibold text-gray-800 mb-4">Customer Sentiment</h3>
          {sentimentData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={sentimentData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                  {sentimentData.map((entry, i) => (
                    <Cell key={i} fill={SENTIMENT_COLORS[entry.name] || '#9ca3af'} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400 text-sm">
              No conversation data yet. Start chatting to see sentiment analysis.
            </div>
          )}
        </Card>
      </div>

      {/* Recent Data */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Leads */}
        <Card>
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-800">Recent Leads</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {data.recent_leads.length === 0 ? (
              <p className="text-center text-gray-400 py-8 text-sm">No leads yet</p>
            ) : data.recent_leads.map((lead) => (
              <div key={lead.id} className="px-6 py-3 flex items-center justify-between hover:bg-gray-50">
                <div>
                  <p className="text-sm font-medium text-gray-800">{lead.name || 'Unknown'}</p>
                  <p className="text-xs text-gray-400">{lead.company || lead.email || 'No details'}</p>
                </div>
                <Badge label={lead.status} />
              </div>
            ))}
          </div>
        </Card>

        {/* Upcoming Appointments */}
        <Card>
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-base font-semibold text-gray-800">Upcoming Appointments</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {data.recent_appointments.length === 0 ? (
              <p className="text-center text-gray-400 py-8 text-sm">No appointments scheduled</p>
            ) : data.recent_appointments.map((appt) => (
              <div key={appt.id} className="px-6 py-3 flex items-center justify-between hover:bg-gray-50">
                <div>
                  <p className="text-sm font-medium text-gray-800">{appt.customer_name}</p>
                  <p className="text-xs text-gray-400">{appt.appointment_date} at {appt.appointment_time}</p>
                </div>
                <Badge label={appt.status} />
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
