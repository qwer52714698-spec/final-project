import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { stocksApi } from '../api/stocksApi'
import { newsApi } from '../api/newsApi'
import StockChart from '../components/StockChart'

function SectorStocks() {
  const { sectorId } = useParams()
  const navigate = useNavigate()
  const [stocksWithPrices, setStocksWithPrices] = useState([])
  const [sector, setSector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    loadStocks()
    loadSectorInfo()
  }, [sectorId, days])

  const loadStocks = async () => {
    try {
      const response = await stocksApi.getSectorStocksWithPrices(sectorId, days)
      setStocksWithPrices(response.data)
    } catch (error) {
      console.error('주식 데이터 로딩 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSectorInfo = async () => {
    try {
      const response = await newsApi.getSectors()
      const foundSector = response.data.find(s => s.id === parseInt(sectorId))
      setSector(foundSector)
    } catch (error) {
      console.error('섹터 정보 로딩 실패:', error)
    }
  }

  const handleCollectPrices = async () => {
    try {
      await stocksApi.collectStockPrices()
      alert('주가 데이터 수집을 시작했습니다. 잠시 후 새로고침 해주세요.')
    } catch (error) {
      console.error('주가 수집 실패:', error)
      alert('주가 수집에 실패했습니다.')
    }
  }

  if (loading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← 돌아가기
          </button>
          <h1 className="text-3xl font-bold">
            {sector?.icon} {sector?.name} 주식
          </h1>
        </div>
        <div className="flex gap-3">
          <select 
            value={days} 
            onChange={(e) => setDays(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-4 py-2"
          >
            <option value={7}>7일</option>
            <option value={30}>30일</option>
            <option value={90}>90일</option>
          </select>
          <button
            onClick={handleCollectPrices}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition"
          >
            주가 수집
          </button>
        </div>
      </div>

      {stocksWithPrices.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          주식 데이터가 없습니다. 주가 수집 버튼을 눌러주세요.
        </div>
      ) : (
        <div className="space-y-6">
          {stocksWithPrices.map(({ stock, prices }) => (
            prices.length > 0 && (
              <StockChart key={stock.id} stock={stock} prices={prices} />
            )
          ))}
        </div>
      )}
    </div>
  )
}

export default SectorStocks
