import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
const api = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });

export const compileCode = async (source) => (await api.post('/compile/', { source })).data;
export const translateCode = async (source) => (await api.post('/translate/', { source })).data;
export const getAST = async (source) => (await api.post('/ast/', { source })).data;
export const debugCode = async (source) => (await api.post('/debug/', { source })).data;
export default api;
