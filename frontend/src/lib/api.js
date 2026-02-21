import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('shopply_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

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
  getOfferte: () => api.get('/prodotti/offerte'),
};

// Liste
export const listeAPI = {
  getAll: () => api.get('/liste'),
  create: (data) => api.post('/liste', data),
  update: (id, data) => api.put(`/liste/${id}`, data),
  delete: (id) => api.delete(`/liste/${id}`),
  condividi: (id, email) => api.post(`/liste/${id}/condividi`, { email_destinatario: email }),
  rimuoviCondivisione: (id, email) => api.delete(`/liste/${id}/condividi/${email}`),
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

// Notifiche
export const notificheAPI = {
  getAll: () => api.get('/notifiche'),
  getNonLette: () => api.get('/notifiche/non-lette'),
  segnaLetta: (id) => api.patch(`/notifiche/${id}/letta`),
  leggiTutte: () => api.patch('/notifiche/leggi-tutte'),
  elimina: (id) => api.delete(`/notifiche/${id}`),
};

// Famiglia
export const famigliaAPI = {
  get: () => api.get('/famiglia'),
  crea: (nome) => api.post(`/famiglia/crea?nome=${encodeURIComponent(nome)}`),
  invita: (email) => api.post('/famiglia/invita', { email }),
  getInviti: () => api.get('/famiglia/inviti'),
  accettaInvito: (id) => api.post(`/famiglia/inviti/${id}/accetta`),
};

// Referral
export const referralAPI = {
  getStats: () => api.get('/referral/stats'),
  getInviti: () => api.get('/referral/inviti'),
  invita: (email) => api.post('/referral/invita', { email }),
  riscatta: (punti) => api.post('/referral/riscatta', null, { params: { punti } }),
  getClassifica: () => api.get('/referral/classifica'),
};

// Prezzi
export const prezziAPI = {
  aggiorna: () => api.post('/prezzi/aggiorna'),
  ultimoAggiornamento: () => api.get('/prezzi/ultimo-aggiornamento'),
};

// Seed
export const seedAPI = {
  seed: () => api.post('/seed'),
};

export default api;
