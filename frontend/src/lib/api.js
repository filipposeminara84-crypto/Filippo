import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('shopply_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('shopply_token');
      localStorage.removeItem('shopply_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

// Supermercati
export const supermercatiAPI = {
  getAll: () => api.get('/supermercati'),
  getById: (id) => api.get(`/supermercati/${id}`),
};

// Prodotti
export const prodottiAPI = {
  getAll: (params) => api.get('/prodotti', { params }),
  autocomplete: (q) => api.get('/prodotti/autocomplete', { params: { q } }),
  getCategorie: () => api.get('/categorie'),
};

// Liste
export const listeAPI = {
  getAll: () => api.get('/liste'),
  create: (data) => api.post('/liste', data),
  delete: (id) => api.delete(`/liste/${id}`),
};

// Ottimizzazione
export const ottimizzaAPI = {
  ottimizza: (data) => api.post('/ottimizza', data),
  getMatricePrezzi: (prodotti) => api.post('/matrice-prezzi', prodotti),
};

// Storico
export const storicoAPI = {
  getAll: () => api.get('/storico'),
  markEseguita: (id) => api.patch(`/storico/${id}/eseguita`),
};

// Preferenze
export const preferenzeAPI = {
  get: () => api.get('/preferenze'),
  update: (data) => api.put('/preferenze', data),
};

// Seed
export const seedAPI = {
  seed: () => api.post('/seed'),
};

export default api;
