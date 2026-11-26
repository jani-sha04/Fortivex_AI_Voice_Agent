import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Mic2, Users, BookOpen, Calendar,
  History, Settings, ChevronLeft, ChevronRight, Zap
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/agent', label: 'AI Voice Agent', icon: Mic2 },
  { path: '/leads', label: 'Lead Management', icon: Users },
  { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
  { path: '/appointments', label: 'Appointments', icon: Calendar },
  { path: '/history', label: 'Call History', icon: History },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <aside
      className={`flex flex-col bg-[#0f172a] text-white transition-all duration-300 ease-in-out min-h-screen ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-700">
        <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex-shrink-0">
          <Zap size={18} className="text-white" />
        </div>
        {!collapsed && (
          <div>
            <div className="font-bold text-base tracking-wide">FORTIVEX</div>
            <div className="text-xs text-slate-400">AI Sales Agent</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`
            }
            title={collapsed ? label : ''}
          >
            <Icon size={18} className="flex-shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="px-2 py-4 border-t border-slate-700">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full px-3 py-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
        >
          {collapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span className="ml-2 text-xs">Collapse</span></>}
        </button>
      </div>

      {/* Version */}
      {!collapsed && (
        <div className="px-4 pb-4 text-xs text-slate-600">v1.0.0 · NovaTech Demo</div>
      )}
    </aside>
  );
}
