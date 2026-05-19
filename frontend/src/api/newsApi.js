import api from './axios'

export const newsApi = {
  getSectors: () => api.get('/news/sectors'),

  getDashboardSummary: () => api.get('/news/dashboard-summary'),

  getNewsBySector: (sectorId, page = 1, size = 20) => 
    api.get(`/news/sector/${sectorId}`, { params: { page, size } }),

  getAllNews: (page = 1, size = 30, sectorId = null) => 
    api.get('/news/', { params: { page, size, sector_id: sectorId } }),

  getStockNews: (symbol, page = 1, size = 1000) => 
    api.get(`/news/stock/${symbol}`, { params: { page, size } }),

  collectNews: (sectorId = null) => 
    api.post('/news/collect', null, { params: { sector_id: sectorId } }),

  analyzeNews: () => api.post('/news/analyze'),

  analyzeSingleNews: (newsId) => api.post(`/news/${newsId}/analyze`),
}