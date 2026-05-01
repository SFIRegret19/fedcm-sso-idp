import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL, // Берем URL из .env
    withCredentials: true // КРИТИЧЕСКИ ВАЖНО: разрешает отправку и прием Cookies
});

export default api;