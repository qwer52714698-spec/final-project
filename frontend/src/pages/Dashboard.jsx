import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'

function Dashboard() {
  const [sectors, setSectors] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const response = await newsApi.getDashboardSummary()
      setSectors(response.data)
    } catch (error) {
      console.error('대시보드 로딩 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTemperatureColor = (temp) => {
    if (temp >= 60) return 'bg-red-500'
    if (temp >= 40) return 'bg-yellow-500'
    return 'bg-blue-500'
  }

  if (loading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">섹터별 시장 현황</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sectors.map(sector => (
          <div key={sector.sector_id} className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <span>{sector.icon}</span>
                {sector.sector_name}
              </h2>
              <div className="text-2xl font-bold" style={{ color: sector.sentiment_temperature >= 50 ? '#ef4444' : '#3b82f6' }}>
                {sector.sentiment_temperature.toFixed(0)}°
              </div>
            </div>

            <div className="mb-4">
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className={`h-3 rounded-full ${getTemperatureColor(sector.sentiment_temperature)}`}
                  style={{ width: `${sector.sentiment_temperature}%` }}
                ></div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-4 text-sm">
              <div className="text-center">
                <div className="text-green-600 font-bold">{sector.positive_count}</div>
                <div className="text-gray-500">긍정</div>
              </div>
              <div className="text-center">
                <div className="text-gray-600 font-bold">{sector.neutral_count}</div>
                <div className="text-gray-500">중립</div>
              </div>
              <div className="text-center">
                <div className="text-red-600 font-bold">{sector.negative_count}</div>
                <div className="text-gray-500">부정</div>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => navigate(`/sector/${sector.sector_id}/news`)}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
              >
                뉴스 보기 ({sector.news_count})
              </button>
              <button
                onClick={() => navigate(`/sector/${sector.sector_id}/stocks`)}
                className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition"
              >
                주식 보기 ({sector.stock_count})
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Dashboard
