import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('adminToken');
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
      localStorage.removeItem('adminToken');
      if (window.location.pathname.startsWith('/admin')) {
        window.location.href = '/admin/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email, password) => api.post('/auth/login', { email, password });
export const getMe = () => api.get('/auth/me');

// Players
export const getPlayers = (params) => api.get('/players', { params });
export const getPlayer = (id) => api.get(`/players/${id}`);
export const getPlayerBySlug = (slug) => api.get(`/players/slug/${slug}`);
export const createPlayer = (data) => api.post('/players', data);
export const updatePlayer = (id, data) => api.put(`/players/${id}`, data);
export const deletePlayer = (id) => api.delete(`/players/${id}`);

// Clubs
export const getClubs = (params) => api.get('/clubs', { params });
export const getClub = (id) => api.get(`/clubs/${id}`);
export const getClubBySlug = (slug) => api.get(`/clubs/slug/${slug}`);
export const createClub = (data) => api.post('/clubs', data);
export const updateClub = (id, data) => api.put(`/clubs/${id}`, data);
export const deleteClub = (id) => api.delete(`/clubs/${id}`);

// Competitions
export const getCompetitions = (params) => api.get('/competitions', { params });
export const getCompetition = (id) => api.get(`/competitions/${id}`);
export const getCompetitionBySlug = (slug) => api.get(`/competitions/slug/${slug}`);
export const createCompetition = (data) => api.post('/competitions', data);
export const updateCompetition = (id, data) => api.put(`/competitions/${id}`, data);
export const deleteCompetition = (id) => api.delete(`/competitions/${id}`);

// Sources
export const getSources = (params) => api.get('/sources', { params });
export const getSource = (id) => api.get(`/sources/${id}`);
export const createSource = (data) => api.post('/sources', data);
export const updateSource = (id, data) => api.put(`/sources/${id}`, data);
export const deleteSource = (id) => api.delete(`/sources/${id}`);

// Events
export const getEvents = (params) => api.get('/events', { params });
export const getEvent = (id) => api.get(`/events/${id}`);
export const createEvent = (data) => api.post('/events', data);
export const updateEvent = (id, data) => api.put(`/events/${id}`, data);
export const deleteEvent = (id) => api.delete(`/events/${id}`);

// Transfers
export const getTransfers = (params) => api.get('/transfers', { params });
export const getConfirmedTransfers = (params) => api.get('/transfers/confirmed', { params });
export const getTransfer = (id) => api.get(`/transfers/${id}`);
export const createTransfer = (data) => api.post('/transfers', data);
export const updateTransfer = (id, data) => api.put(`/transfers/${id}`, data);
export const deleteTransfer = (id) => api.delete(`/transfers/${id}`);

// Rumours
export const getRumours = (params) => api.get('/rumours', { params });
export const getRumour = (id) => api.get(`/rumours/${id}`);
export const createRumour = (data) => api.post('/rumours', data);
export const updateRumour = (id, data) => api.put(`/rumours/${id}`, data);
export const deleteRumour = (id) => api.delete(`/rumours/${id}`);

// Articles
export const getArticles = (params) => api.get('/articles', { params });
export const getPublishedArticles = (params) => api.get('/articles/published', { params });
export const getBreakingNews = (params) => api.get('/articles/breaking', { params });
export const getArticle = (id) => api.get(`/articles/${id}`);
export const getArticleBySlug = (slug) => api.get(`/articles/slug/${slug}`);
export const getArticlesByPlayer = (playerId, params) => api.get(`/articles/player/${playerId}`, { params });
export const getArticlesByClub = (clubId, params) => api.get(`/articles/club/${clubId}`, { params });
export const getArticlesByCompetition = (competitionId, params) => api.get(`/articles/competition/${competitionId}`, { params });
export const createArticle = (data) => api.post('/articles', data);
export const updateArticle = (id, data) => api.put(`/articles/${id}`, data);
export const deleteArticle = (id) => api.delete(`/articles/${id}`);

// Ad Slots
export const getAdSlots = (params) => api.get('/ad-slots', { params });
export const getActiveAdSlots = (params) => api.get('/ad-slots/active', { params });
export const getAdSlot = (id) => api.get(`/ad-slots/${id}`);
export const getAdSlotByKey = (key) => api.get(`/ad-slots/key/${key}`);
export const createAdSlot = (data) => api.post('/ad-slots', data);
export const updateAdSlot = (id, data) => api.put(`/ad-slots/${id}`, data);
export const deleteAdSlot = (id) => api.delete(`/ad-slots/${id}`);

// Settings
export const getSettings = () => api.get('/settings');
export const getSetting = (key) => api.get(`/settings/${key}`);
export const updateSetting = (key, data) => api.put(`/settings/${key}`, data);

// Search
export const search = (q, limit) => api.get('/search', { params: { q, limit } });
export const autosuggest = (q, limit) => api.get('/search/autosuggest', { params: { q, limit } });

// Stats
export const getDashboardStats = () => api.get('/stats/dashboard');

// Init
export const initAdmin = () => api.post('/init/admin');
export const initAdSlots = () => api.post('/init/ad-slots');

// Users
export const getUsers = () => api.get('/users');
export const createUser = (data) => api.post('/users', data);

export default api;
