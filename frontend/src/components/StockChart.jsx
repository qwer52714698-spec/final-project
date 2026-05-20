import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { stocksApi } from '../api/stocksApi'

function StockChart({ stock, prices }) {
  const navigate = useNavigate()
  const [prediction, setPrediction] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  const chartData = prices?.map(p => ({
    date: new Date(p.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    종가: p.close,
    고가: p.high,
    저가: p.low,
    예측종가: null
  })) || []

  const chartDataWithPrediction = (() => {
    if (!prediction || chartData.length === 0) return chartData;
    
    const lastActualData = chartData[chartData.length - 1];
    const updatedChartData = chartData.map(d => ({ ...d }));
    
    updatedChartData[updatedChartData.length - 1].예측종가 = lastActualData.종가;
    
    let targetPrice = prediction.predicted_next_close;
    if (prediction.prediction === '상승' && targetPrice <= lastActualData.종가) {
      targetPrice = lastActualData.종가 * 1.015;
    } else if (prediction.prediction === '하락' && targetPrice >= lastActualData.종가) {
      targetPrice = lastActualData.종가 * 0.985;
    } else if (prediction.prediction === '횡보') {
      targetPrice = lastActualData.종가;
    }

    updatedChartData.push({
      date: '내일(예측)',
      종가: null,
      고가: null,
      저가: null,
      예측종가: Math.round(targetPrice),
    });
    
    return updatedChartData;
  })();

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

  const formatYAxis = (tickItem) => {
    if (tickItem >= 100000) {
      return `${Math.round(tickItem / 10000) * 1}만`;
    }
    return tickItem.toLocaleString();
  };

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

      <div className="flex flex-col lg:flex-row gap-6 items-stretch">
        <div className="flex-1 min-w-0 flex flex-col justify-center">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartDataWithPrediction} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis 
                domain={[dataMin => Math.floor((dataMin * 0.96) / 5000) * 5000, dataMax => Math.ceil((dataMax * 1.04) / 5000) * 5000]} 
                tickFormatter={formatYAxis}
              />
              <Tooltip formatter={(value) => value ? `${value.toLocaleString()}원` : '-'} />
              <Legend />
              <Line type="monotone" dataKey="종가" stroke="#2563eb" strokeWidth={2} connectNulls={false} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="고가" stroke="#10b981" strokeWidth={1} connectNulls={false} dot={false} />
              <Line type="monotone" dataKey="저가" stroke="#ef4444" strokeWidth={1} connectNulls={false} dot={false} />
              {prediction && (
                <Line type="monotone" dataKey="예측종가" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 5, fill: '#f59e0b' }} connectNulls={true} />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {prediction && (
          <div className="w-full lg:w-72 shrink-0 flex flex-col justify-between gap-3 border-l lg:border-l border-gray-100 lg:pl-4">
            <div className={`rounded-lg border p-3 text-center ${style.bg} ${style.border}`}>
              <div className="text-xs text-gray-500 mb-1">내일 방향 예측</div>
              <div className={`text-2xl font-bold ${style.color}`}>
                {style.icon} {prediction.prediction}
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-2 text-center font-semibold">최근 5영업일 누적 성과</div>
              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center">
                  <span className="flex items-center gap-1">
                    <span className="text-xs text-gray-500">실제 수익률</span>
                    <span className="relative group">
                      <span className="text-xs text-gray-400 bg-gray-200 rounded-full w-3.5 h-3.5 flex items-center justify-center cursor-help leading-none">?</span>
                      <span className="absolute left-0 bottom-full mb-1 w-44 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-normal">
                        5일치 일별 실제 수익률의 합계
                      </span>
                    </span>
                  </span>
                  <span className={`text-sm font-bold ${prediction.actual_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {prediction.actual_return >= 0 ? '+' : ''}{prediction.actual_return}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="flex items-center gap-1">
                    <span className="text-xs text-gray-500">예측 수익률</span>
                    <span className="relative group">
                      <span className="text-xs text-gray-400 bg-gray-200 rounded-full w-3.5 h-3.5 flex items-center justify-center cursor-help leading-none">?</span>
                      <span className="absolute left-0 bottom-full mb-1 w-48 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-normal">
                        XGBoost가 예측한 다음날 종가 기준 5일치 일별 예측 수익률의 합계
                      </span>
                    </span>
                  </span>
                  <span className={`text-sm font-bold ${prediction.predicted_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {prediction.predicted_return >= 0 ? '+' : ''}{prediction.predicted_return}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="flex items-center gap-1">
                    <span className="text-xs text-gray-500">방향 적중률</span>
                    <span className="relative group">
                      <span className="text-xs text-gray-400 bg-gray-200 rounded-full w-3.5 h-3.5 flex items-center justify-center cursor-help leading-none">?</span>
                      <span className="absolute left-0 bottom-full mb-1 w-44 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none whitespace-normal">
                        5일 중 AI의 상하방 예측이 실제 시장 결과와 일치한 비율
                      </span>
                    </span>
                  </span>
                  <span className={`text-sm font-bold ${prediction.win_rate >= 60 ? 'text-green-600' : 'text-gray-700'}`}>
                    {prediction.win_rate}%
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5">
              <div className="text-[10px] text-slate-500 mb-2 text-center font-bold tracking-wider">과거 AI 방향 예측 실적 검증</div>
              <div className="flex flex-col gap-1 text-[11px]">
                {prediction.history_log && prediction.history_log.map((log, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-white px-2 py-1 rounded border border-slate-100 gap-1">
                    <span className="text-slate-400 text-[10px] shrink-0">{log.date}</span>
                    <div className="flex items-center gap-1.5 flex-1 justify-center text-[10px] text-slate-600">
                      <span>[예측] {log.predicted}</span>
                      <span className="text-slate-300">|</span>
                      <span>[실제] {log.actual}</span>
                    </div>
                    <span className={`font-bold text-xs shrink-0 ${log.is_correct ? 'text-emerald-500' : 'text-rose-500'}`}>
                      {log.is_correct ? '정확' : '실패'}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-gray-100 pt-2">
              <div className="text-xs text-gray-400 mb-2">핵심 주가 변동 요인</div>
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

            <div className="text-[10px] text-gray-400 text-center mt-1">
              분석 기준일: {prediction.analysis_date}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StockChart