import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'

function GaugeMeter({ positive, neutral, negative, temperature }) {
  const total = positive + neutral + negative
  if (total === 0) return null

  const score = (positive - negative) / total
  const needleAngle = -180 + ((score + 1) / 2) * 180

  const cx = 80, cy = 80, r = 60, strokeW = 11

  function arcPath(startDeg, endDeg, radius) {
    const s = (startDeg * Math.PI) / 180
    const e = (endDeg * Math.PI) / 180
    const largeArc = Math.abs(endDeg - startDeg) > 180 ? 1 : 0
    return `M ${cx + radius * Math.cos(s)} ${cy + radius * Math.sin(s)} A ${radius} ${radius} 0 ${largeArc} 1 ${cx + radius * Math.cos(e)} ${cy + radius * Math.sin(e)}`
  }

  const posRatio = positive / total
  const negRatio = negative / total
  const posEnd = -180 + posRatio * 180
  const negStart = -negRatio * 180

  const needleLength = r - 8
  const nx = cx + needleLength * Math.cos((needleAngle * Math.PI) / 180)
  const ny = cy + needleLength * Math.sin((needleAngle * Math.PI) / 180)

  const needleColor =
    temperature >= 58 ? '#E24B4A'
    : temperature >= 53 ? '#BA7517'
    : temperature >= 47 ? '#888780'
    : temperature >= 42 ? '#378ADD'
    : '#185FA5'

  return (
    <svg width="160" height="88" viewBox="0 0 160 88">
      <path d={arcPath(-180, 0, r)} fill="none" stroke="#E5E5E3" strokeWidth={strokeW} strokeLinecap="round" />
      <path d={arcPath(-180, posEnd, r)} fill="none" stroke="#639922" strokeWidth={strokeW} strokeLinecap="round" />
      <path d={arcPath(negStart, 0, r)} fill="none" stroke="#E24B4A" strokeWidth={strokeW} strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={needleColor} strokeWidth="3" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="5" fill={needleColor} />
    </svg>
  )
}

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

  const getTempInfo = (temp) => {
    if (temp >= 58) return { label: '과열', textColor: 'text-red-600',  badgeBg: 'bg-red-50 text-red-800' }
    if (temp >= 53) return { label: '상승', textColor: 'text-amber-600', badgeBg: 'bg-amber-50 text-amber-800' }
    if (temp >= 47) return { label: '중립', textColor: 'text-gray-500',  badgeBg: 'bg-gray-100 text-gray-600' }
    if (temp >= 42) return { label: '하락', textColor: 'text-blue-600',  badgeBg: 'bg-blue-50 text-blue-800' }
    return                 { label: '급락', textColor: 'text-blue-800',  badgeBg: 'bg-blue-100 text-blue-900' }
  }

  if (loading) {
    return <div className="text-center py-20 text-gray-400">로딩 중...</div>
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6 text-gray-900">섹터별 시장 현황</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sectors.map(sector => {
          const temp = Math.round(sector.sentiment_temperature)
          const { label, textColor, badgeBg } = getTempInfo(temp)

          return (
            <div
              key={sector.sector_id}
              className="bg-white rounded-xl border border-gray-100 p-4 flex flex-col items-center gap-2"
            >
              <div className="w-full flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{sector.icon}</span>
                  <span className="text-lg font-bold text-gray-900">{sector.sector_name}</span>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className={`text-xl font-semibold ${textColor}`}>{temp}°</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeBg}`}>{label}</span>
                </div>
              </div>

              <GaugeMeter
                positive={sector.positive_count}
                neutral={sector.neutral_count}
                negative={sector.negative_count}
                temperature={temp}
              />

              <div className="w-full flex justify-between pt-3 border-t border-gray-100">
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="w-2 h-2 rounded-full bg-green-600 inline-block"></span>
                  <span className="text-green-700">↑ 호재 {sector.positive_count}</span>
                </div>
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="w-2 h-2 rounded-full bg-gray-400 inline-block"></span>
                  <span className="text-gray-500">중립 {sector.neutral_count}</span>
                </div>
                <div className="flex items-center gap-1.5 text-sm">
                  <span className="w-2 h-2 rounded-full bg-red-500 inline-block"></span>
                  <span className="text-red-600">↓ 악재 {sector.negative_count}</span>
                </div>
              </div>

              <div className="w-full flex gap-2">
                <button
                  onClick={() => navigate(`/sector/${sector.sector_id}/news`)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-sm font-medium border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                >
                  📰 뉴스 <span className="text-gray-400">{sector.news_count}</span>
                </button>
                <button
                  onClick={() => navigate(`/sector/${sector.sector_id}/stocks`)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 text-sm font-medium border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                >
                  📈 주식 <span className="text-gray-400">{sector.stock_count}</span>
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Dashboard