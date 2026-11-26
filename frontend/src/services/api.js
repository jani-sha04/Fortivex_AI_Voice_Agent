import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

// ---- Agent ----
export const agentAPI = {
  chat: (message, sessionId, conversationId) =>
    api.post('/api/agent/chat', { message, session_id: sessionId, conversation_id: conversationId }),
  qualify: (conversationId, sessionId) =>
    api.post('/api/agent/qualify', { conversation_id: conversationId, session_id: sessionId }),
  sentiment: (text) =>
    api.post('/api/agent/sentiment', { text }),
  status: () => api.get('/api/agent/status'),
};

// ---- Voice ----
export const voiceAPI = {
  transcribe: (audioBlob) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    return api.post('/api/voice/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  speak: (text) => {
    const formData = new FormData();
    formData.append('text', text);
    return api.post('/api/voice/speak', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob',
    });
  },
  status: () => api.get('/api/voice/status'),
};

// ---- Knowledge Base ----
export const knowledgeAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  list: () => api.get('/api/knowledge/documents'),
  delete: (docId) => api.delete(`/api/knowledge/documents/${docId}`),
};

// ---- Leads ----
export const leadsAPI = {
  list: (params) => api.get('/api/leads', { params }),
  get: (id) => api.get(`/api/leads/${id}`),
  create: (data) => api.post('/api/leads', data),
  update: (id, data) => api.put(`/api/leads/${id}`, data),
};

// ---- Appointments ----
export const appointmentsAPI = {
  list: () => api.get('/api/appointments'),
  create: (data) => api.post('/api/appointments', data),
  update: (id, data) => api.put(`/api/appointments/${id}`, data),
  cancel: (id) => api.delete(`/api/appointments/${id}`),
  availableSlots: () => api.get('/api/appointments/available-slots'),
};

// ---- Conversations ----
export const conversationsAPI = {
  list: () => api.get('/api/conversations'),
  get: (id) => api.get(`/api/conversations/${id}`),
  getSummary: (id) => api.get(`/api/conversations/${id}/summary`),
  end: (id) => api.post(`/api/conversations/${id}/end`),
};

// ---- Dashboard ----
export const dashboardAPI = {
  analytics: () => api.get('/api/dashboard/analytics'),
};

export default api;
