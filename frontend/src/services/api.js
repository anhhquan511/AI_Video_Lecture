import axios from 'axios';

// Địa chỉ Backend
const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const videoApi = {
  createVideo: (data) => api.post('/video/create', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),

  getAllVideos: () => api.get('/video/list'),

  getVideoDetail: (jobId) => api.get(`/video/status/${jobId}`),
  
  getDocuments: () => api.get('/video/documents'), 

  deleteVideo: (jobId) => api.delete(`/video/delete/${jobId}`),
};

export default api;