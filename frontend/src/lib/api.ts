import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const getPrograms = (filters?: any) => api.get('/programs', { params: filters });
export const getProgram = (id: string) => api.get(`/programs/${id}`);
export const getProgramAssets = (id: string) => api.get(`/programs/${id}/assets`);
export const getProgramEndpoints = (id: string, filters?: any) => api.get(`/programs/${id}/endpoints`, { params: filters });
export const getProgramReports = (id: string) => api.get(`/programs/${id}/reports`);

export const login = (data: any) => api.post('/auth/login', data);
export const register = (data: any) => api.post('/auth/register', data);

export const getWatchlist = () => api.get('/watchlist');
export const addToWatchlist = (programId: string) => api.post(`/watchlist/${programId}`);
export const removeFromWatchlist = (programId: string) => api.delete(`/watchlist/${programId}`);

export const getPreferences = () => api.get('/preferences');
export const updatePreferences = (prefs: any) => api.put('/preferences', prefs);

export default api;
