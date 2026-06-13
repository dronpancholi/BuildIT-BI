import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  register: (data: { email: string; password: string; full_name: string; role: string }) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data: { full_name?: string; email?: string }) =>
    api.put('/auth/me', data),
};

const v2 = axios.create({
  baseURL: `${API_BASE_URL}/api/v2`,
  headers: { 'Content-Type': 'application/json' },
});

v2.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

v2.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob') {
      return response;
    }

    if (
      response.data &&
      typeof response.data === 'object' &&
      response.data.status === 'success' &&
      'data' in response.data
    ) {
      return { ...response, data: response.data.data };
    }
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const executiveAPI = {
  getKPIs: (params?: { start_date?: string; end_date?: string }) =>
    v2.get('/executive/kpis', { params }),
  getAlerts: () =>
    v2.get('/executive/alerts'),
  getBriefing: () =>
    v2.get('/executive/briefing'),
};

export const forecastingAPI = {
  getForecasts: (params?: { metric_type?: string; periods_ahead?: number }) =>
    v2.get('/forecasting', { params }),
};

export const analyticsAPI = {
  getMetrics: (params?: { dimension?: string; start_date?: string; end_date?: string }) =>
    v2.get('/analytics/metrics', { params }),
};

export const exportsAPI = {
  exportBoardPack: (format: 'pdf' | 'excel' | 'ppt') =>
    v2.post(`/exports/board-pack?format=${format}`, {}, { responseType: 'blob' }),
};

export const assistantAPI = {
  askQuestion: (question: string) =>
    v2.post('/executive_assistant/ask', { question }),
};

export const dataImportAPI = {
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return v2.post('/data_import/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
};
