import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { stocksApi } from '../api/stocksApi'

function StockChart({ stock, prices }) {
  const navigate = useNavigate()
  const [prediction, setPrediction] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  const chartData = prices.map(p => ({
    date: new Date(p.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    종가: p.close,
    고가: p.high,
    저가: p.low,
  }))

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setError(null)
    try {
      const response = await stocksApi.analyzeStock(stock.symbol)
      setPrediction(response.data.data)
    } catch (e) {
      setError('분석에 실패했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setAnalyzing(false)
    }
  }

  const getPredictionStyle = (pred) => {
    if (pred === '상승') return { color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', icon: '↑' }
    if (pred === '하락') return { color: 'text-red-600',   bg: 'bg-red-50',   border: 'border-red-200',   icon: '↓' }
    return               { color: 'text-gray-500',  bg: 'bg-gray-50',  border: 'border-gray-200',  icon: '→' }
  }

  const style = prediction ? getPredictionStyle(prediction.prediction) : null

  const maxFactor = prediction
    ? Math.max(...Object.values(prediction.top_influencers))
    : 1

  const factorLabel = {
    Close:         '종가',
    Volume:        '거래량',
    interest_rate: '금리',
    exchange_rate: '환율',
    oil_price:     '유가',
    sp500:         'S&P500',
    inst_5d:       '기관 순매수',
    foreign_5d:    '외국인 순매수',
    volatility:    '변동성',
    val_score:     '밸류에이션',
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 
          onClick={() => navigate(`/stock/${stock.symbol}/news`)}
          className="text-xl font-bold cursor-pointer hover:text-blue-600 hover:underline inline-block"
        >
          {stock.name} ({stock.symbol})
        </h3>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {analyzing ? '분석 중...' : '🤖 AI 예측'}
        </button>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}

      <div className={`flex gap-4 ${prediction ? 'items-start' : ''}`}>
        <div className="flex-1 min-w-0">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="종가" stroke="#2563eb" strokeWidth={2} />
              <Line type="monotone" dataKey="고가" stroke="#10b981" strokeWidth={1} />
              <Line type="monotone" dataKey="저가" stroke="#ef4444" strokeWidth={1} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {prediction && (
          <div className="w-48 shrink-0 flex flex-col gap-3">
            <div className={`rounded-lg border p-3 text-center ${style.bg} ${style.border}`}>
              <div className="text-xs text-gray-500 mb-1">내일 예측</div>
              <div className={`text-2xl font-bold ${style.color}`}>
                {style.icon} {prediction.prediction}
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-2 text-center">최근 5영업일 수익률</div>
              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">실제 수익률</span>
                  <span className={`text-sm font-bold ${prediction.actual_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {prediction.actual_return >= 0 ? '+' : ''}{prediction.actual_return}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">예측 수익률</span>
                  <span className={`text-sm font-bold ${prediction.predicted_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {prediction.predicted_return >= 0 ? '+' : ''}{prediction.predicted_return}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">승률</span>
                  <span className={`text-sm font-bold ${prediction.win_rate >= 60 ? 'text-green-600' : 'text-gray-700'}`}>
                    {prediction.win_rate}%
                  </span>
                </div>
                <div className="text-xs text-gray-400 text-center mt-1">
                  {prediction.period_start} ~ {prediction.period_end}
                </div>
              </div>
            </div>

            <div className="border-t border-gray-100 pt-2">
              <div className="text-xs text-gray-400 mb-2">주요 영향 요인</div>
              <div className="flex flex-col gap-1.5">
                {Object.entries(prediction.top_influencers).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-gray-600">{factorLabel[key] || key}</span>
                      <span className="text-gray-800 font-medium">{val.toFixed(2)}</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(val / maxFactor) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="text-xs text-gray-400 text-center">
              기준일: {prediction.analysis_date}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StockChart