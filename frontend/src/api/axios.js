import axios from 'axios';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://final-project-56uc.onrender.com',
  timeout: 60000, // 
  headers: {
    'Content-Type': 'application/json'
  }
});

export default instance;