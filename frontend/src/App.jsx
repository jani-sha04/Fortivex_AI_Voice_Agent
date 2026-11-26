import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import AgentPage from './pages/AgentPage';
import LeadsPage from './pages/LeadsPage';
import KnowledgePage from './pages/KnowledgePage';
import AppointmentsPage from './pages/AppointmentsPage';
import CallHistoryPage from './pages/CallHistoryPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agent" element={<AgentPage />} />
            <Route path="/leads" element={<LeadsPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/appointments" element={<AppointmentsPage />} />
            <Route path="/history" element={<CallHistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
