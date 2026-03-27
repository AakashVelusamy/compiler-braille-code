import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

export async function compileCode(source) {
  const response = await api.post('/compile/', { source });
  return response.data;
}

export async function translateCode(source) {
  const response = await api.post('/translate/', { source });
  return response.data;
}

export async function getAST(source) {
  const response = await api.post('/ast/', { source });
  return response.data;
}

export default api;
