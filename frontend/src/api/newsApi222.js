import api from './axios'

export const newsApi = {
  getSectors: () => api.get('/news/sectors'),

  getDashboardSummary: () => api.get('/news/dashboard-summary'),

  getNewsBySector: (sectorId, page = 1, size = 10) => 
    api.get(`/news/sector/${sectorId}`, { params: { page, size } }),

  getAllNews: (page = 1, size = 10, sectorId = null) => 
    api.get('/news/', { params: { page, size, sector_id: sectorId } }),

  // ✅ 개별 뉴스 조회 (마이페이지 뉴스 보러가기용)
  getNewsById: (newsId) => api.get(`/news/${newsId}`),

  collectNews: (sectorId = null) => 
    api.post('/news/collect', null, { params: { sector_id: sectorId } }),

  analyzeNews: () => api.post('/news/analyze'),

  // 🆕 개별 뉴스 AI 감성분석
  analyzeSingleNews: (newsId) => api.post(`/news/${newsId}/analyze`),
}
