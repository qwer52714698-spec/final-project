import api from './axios'

export const stocksApi = {
  getStocks: (sectorId = null) => 
    api.get('/stocks/', { params: { sector_id: sectorId } }),

  getSectorStocksWithPrices: (sectorId, days = 30) => 
    api.get(`/stocks/sector/${sectorId}`, { params: { days } }),

  getStockPrices: (symbol, days = 30) => 
    api.get(`/stocks/${symbol}/prices`, { params: { days } }),

  collectStockPrices: () => api.post('/stocks/collect'),
}
