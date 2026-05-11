import api from './axios'

export const newsApi = {
  getSectors: () => api.get('/news/sectors'),

  getDashboardSummary: () => api.get('/news/dashboard-summary'),

  getNewsBySector: (sectorId, limit = 20, skip = 0) => 
    api.get(`/news/sector/${sectorId}`, { params: { limit, skip } }),

  getAllNews: (limit = 30, skip = 0, sectorId = null) => 
    api.get('/news/', { params: { limit, skip, sector_id: sectorId } }),

  collectNews: (sectorId = null) => 
    api.post('/news/collect', null, { params: { sector_id: sectorId } }),

  analyzeNews: () => api.post('/news/analyze'),

  analyzeSingleNews: (newsId) => api.post(`/news/${newsId}/analyze`),
}
