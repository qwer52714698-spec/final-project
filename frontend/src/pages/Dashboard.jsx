import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'
import axios from 'axios'

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
    : temperature >= 47 ? '#88780'
    : temperature >= 42 ? '#378ADD'
    : '#185FA5'

  return (
    <svg width="160" height="88" viewBox="0 0 160 88" className="mx-auto mt-2">
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
  const [macroData, setMacroData] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [schedules, setSchedules] = useState([])
  const [selectedSector, setSelectedSector] = useState(1)
  const [sectorDetail, setSectorDetail] = useState(null)
  const [sectorLoading, setSectorLoading] = useState(false)
  const [openGauges, setOpenGauges] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    const fetchMainDashboard = async () => {
      try {
        const response = await axios.get('http://localhost:8000/dashboard/main')
        setMacroData(response.data.macro)
        setAnomalies(response.data.anomalies)
        setSchedules(response.data.schedules)
      } catch (error) {
        console.error('거시 경제 대시보드 로딩 실패:', error)
      }
    }

    const fetchSectors = async () => {
      try {
        const response = await newsApi.getDashboardSummary()
        setSectors(response.data)
      } catch (error) {
        console.error('대시보드 섹터 요약 로딩 실패:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchMainDashboard()
    fetchSectors()
  }, [])

  useEffect(() => {
    const fetchSectorDetail = async () => {
      setSectorLoading(true)
      try {
        const response = await axios.get(`http://localhost:8000/dashboard/sector/${selectedSector}/detail`)
        setSectorDetail(response.data)
      } catch (error) {
        console.error('섹터 정밀 데이터 로딩 실패:', error)
      } finally {
        setSectorLoading(false)
      }
    }
    fetchSectorDetail()
  }, [selectedSector])

  const toggleGauge = (id, e) => {
    e.stopPropagation()
    setOpenGauges(prev => ({ ...prev, [id]: !prev[id] }))
  }

  const handleNewsRedirectToDetail = (newsId, e) => {
    e.stopPropagation()
    if (newsId) {
      // 🔗 [교정 핵심] 엉뚱한 화면 분기를 차단하고 특정 뉴스 ID 타겟팅 쿼리스트링 전달 포워딩
      navigate(`/sector/${selectedSector}/news?newsId=${newsId}`)
    }
  }

  const getTempInfo = (temp) => {
    if (temp >= 58) return { label: '과열', textColor: 'text-red-600',  badgeBg: 'bg-red-50 text-red-800' }
    if (temp >= 53) return { label: '상승', textColor: 'text-amber-600', badgeBg: 'bg-amber-50 text-amber-800' }
    if (temp >= 47) return { label: '중립', textColor: 'text-gray-500',  badgeBg: 'bg-gray-100 text-gray-600' }
    if (temp >= 42) return { label: '하락', textColor: 'text-blue-600',  badgeBg: 'bg-blue-50 text-blue-800' }
    return                 { label: '급락', textColor: 'text-blue-800',  badgeBg: 'bg-blue-100 text-blue-900' }
  }

  const getMarketStatusText = (score) => {
    if (score >= 75) return { status: '극단적 낙관 무드', desc: '호재 오피니언의 비중이 압도적이며, 긍정 여론이 지배하여 시장 전반에 강력한 매수 모멘텀이 작용 중입니다.', color: 'text-emerald-600', bg: 'bg-emerald-50/50' }
    if (score >= 55) return { status: '낙관 우위 무드', desc: '전반적으로 호재성 뉴스가 우세를 점하고 있어 시장 참여자들의 심리가 안정되고 점진적 우상향이 기대됩니다.', color: 'text-green-600', bg: 'bg-green-50/50' }
    if (score >= 45) return { status: '균형 정체 무드', desc: '호재와 악재 오피니언이 팽팽한 대치 상태를 이루며, 뚜렷한 방향성 없이 강력한 관망세가 유지되고 있습니다.', color: 'text-gray-600', bg: 'bg-gray-50' }
    if (score >= 25) return { status: '위축 공포 무드', desc: '리스크 및 악재 뉴스의 노출 빈도가 급증함에 따라 투자자 투심이 동결되고 매도 압력이 유발되는 구간입니다.', color: 'text-orange-600', bg: 'bg-orange-50/50' }
    return { status: '극단적 위기 패닉', desc: '악재 중심의 극단적 여론이 관측 시스템을 점령했으며, 패닉 셀링 등 자본 유출 신호가 감지되는 경보 상태입니다.', color: 'text-red-600', bg: 'bg-red-50/50' }
  }

  if (loading) {
    return <div className="text-center py-20 text-gray-400 font-medium">로딩 중...</div>
  }

  const sentimentScore = macroData?.fear_greed_score || 50
  const marketReport = getMarketStatusText(sentimentScore)

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-gray-950 tracking-tight">📊 마켓무드 모니터링 관제 대시보드</h1>
        <p className="text-xs text-gray-400 mt-1">
          관제 데이터 최종 동기화 시각: {macroData ? new Date(macroData.updated_at).toLocaleString() : '-'}
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
        <div className="xl:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-gray-900 border-b pb-2">🎯 섹터별 시장 체온계 현황</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sectors.map(sector => {
              const temp = Math.round(sector.sentiment_temperature)
              const { label, textColor, badgeBg } = getTempInfo(temp)
              const isSelected = selectedSector === sector.sector_id
              const isGaugeOpen = !!openGauges[sector.sector_id]

              return (
                <div
                  key={sector.sector_id}
                  onClick={() => setSelectedSector(sector.sector_id)}
                  className={`bg-white rounded-xl p-4 flex flex-col gap-3 cursor-pointer transition border shadow-sm ${
                    isSelected ? 'border-2 border-slate-800 bg-slate-50/30' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="w-full flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{sector.icon}</span>
                      <span className="text-base font-bold text-gray-900">{sector.sector_name}</span>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className={`text-lg font-bold ${textColor}`}>{temp}°</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${badgeBg}`}>{label}</span>
                    </div>
                  </div>

                  <div className="w-full flex justify-between text-[11px] bg-gray-50 p-2 rounded-lg border border-gray-100">
                    <span className="text-green-700 font-bold">호재 {sector.positive_count}</span>
                    <span className="text-gray-500 font-bold">중립 {sector.neutral_count}</span>
                    <span className="text-red-600 font-bold">악재 {sector.negative_count}</span>
                  </div>

                  {isGaugeOpen && (
                    <div className="py-2 bg-gray-50/40 border border-dashed border-gray-200 rounded-xl">
                      <GaugeMeter
                        positive={sector.positive_count}
                        neutral={sector.neutral_count}
                        negative={sector.negative_count}
                        temperature={temp}
                      />
                    </div>
                  )}

                  <div className="w-full flex gap-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={(e) => toggleGauge(sector.sector_id, e)}
                      className={`flex-1 py-1.5 text-xs font-bold border rounded-lg transition ${
                        isGaugeOpen ? 'bg-slate-800 border-slate-800 text-white' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      {isGaugeOpen ? '▲ 게이지 접기' : '📊 체온계 보기'}
                    </button>
                    <button
                      onClick={() => navigate(`/sector/${sector.sector_id}/news`)}
                      className="px-3 py-1.5 text-xs font-bold border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                    >
                      📰 뉴스 {sector.news_count}
                    </button>
                    <button
                      onClick={() => navigate(`/sector/${sector.sector_id}/stocks`)}
                      className="px-3 py-1.5 text-xs font-bold border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                    >
                      📈 주식 {sector.stock_count}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="xl:col-span-1 bg-white p-4 rounded-2xl border border-gray-100 shadow-sm mt-0 xl:mt-9 flex flex-col gap-4">
          {sectorLoading ? (
            <div className="text-center py-20 text-xs text-gray-400 font-medium">데이터 스트리밍 중...</div>
          ) : sectorDetail ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b pb-2">
                <h3 className="text-sm font-black text-gray-800">
                  📌 {sectors.find(s => s.sector_id === selectedSector)?.sector_name || '반도체'} 리포트
                </h3>
                <span className="text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-100 px-2 py-0.5 rounded-full">
                  {sectorDetail.sentiment_status}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-1.5">
                <div className="bg-gray-50 p-2 rounded-xl text-center">
                  <span className="text-[9px] text-gray-400 block">외인 누적</span>
                  <span className={`text-[11px] font-black ${sectorDetail.foreigner_net_buy >= 0 ? 'text-red-500' : 'text-blue-500'}`}>
                    {sectorDetail.foreigner_net_buy >= 0 ? '+' : ''}{Math.round(sectorDetail.foreigner_net_buy)}억
                  </span>
                </div>
                <div className="bg-gray-50 p-2 rounded-xl text-center">
                  <span className="text-[9px] text-gray-400 block">기관 누적</span>
                  <span className={`text-[11px] font-black ${sectorDetail.institutional_net_buy >= 0 ? 'text-red-500' : 'text-blue-500'}`}>
                    {sectorDetail.institutional_net_buy >= 0 ? '+' : ''}{Math.round(sectorDetail.institutional_net_buy)}억
                  </span>
                </div>
                <div className="bg-gray-50 p-2 rounded-xl text-center">
                  <span className="text-[9px] text-gray-400 block">공매도 평균</span>
                  <span className="text-[11px] font-black text-gray-700">{sectorDetail.short_selling_ratio}%</span>
                </div>
              </div>

              <div className="bg-amber-50/60 border border-amber-100 p-2 rounded-xl flex gap-1 items-start">
                <span className="text-xs">💡</span>
                <p className="text-[11px] text-amber-900 leading-relaxed font-semibold">
                  {sectorDetail.investment_tip}
                </p>
              </div>

              <div className="border-t pt-3 space-y-3">
                <div>
                  <span className="text-[11px] font-black text-emerald-700 block mb-1">📈 주요 호재 뉴스 Top 5</span>
                  <div className="space-y-1">
                    {sectorDetail.top_positive_news && sectorDetail.top_positive_news.length > 0 ? (
                      sectorDetail.top_positive_news.map((news, idx) => (
                        <div 
                          key={news.id} 
                          onClick={(e) => handleNewsRedirectToDetail(news.id, e)}
                          className="text-[11px] text-gray-700 truncate font-medium hover:text-emerald-600 hover:underline cursor-pointer transition flex justify-between items-center"
                        >
                          <span className="truncate flex-1">
                            <span className="text-emerald-500 font-bold mr-1">{idx + 1}.</span> {news.title}
                          </span>
                          <span className="text-[10px] text-emerald-600 bg-emerald-50 font-bold px-1.5 py-0.5 rounded ml-2 shrink-0">
                            +{Math.round((news.sentiment_score || 0) * 100)}pt
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-[10px] text-gray-400">수집된 호재 뉴스가 없습니다.</div>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-black text-red-600 block mb-1">📉 주요 악재 뉴스 Top 5</span>
                  <div className="space-y-1">
                    {sectorDetail.top_negative_news && sectorDetail.top_negative_news.length > 0 ? (
                      sectorDetail.top_negative_news.map((news, idx) => (
                        <div 
                          key={news.id} 
                          onClick={(e) => handleNewsRedirectToDetail(news.id, e)}
                          className="text-[11px] text-gray-700 truncate font-medium hover:text-red-500 hover:underline cursor-pointer transition flex justify-between items-center"
                        >
                          <span className="truncate flex-1">
                            <span className="text-red-400 font-bold mr-1">{idx + 1}.</span> {news.title}
                          </span>
                          <span className="text-[10px] text-red-600 bg-red-50 font-bold px-1.5 py-0.5 rounded ml-2 shrink-0">
                            -{Math.round(Math.abs(news.sentiment_score || 0) * 100)}pt
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-[10px] text-gray-400">수집된 악재 뉴스가 없습니다.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-xs text-gray-400">섹터를 선택해 주세요.</div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
          <h2 className="text-sm font-bold text-gray-700 mb-3">📰 실시간 뉴스 감성 정밀 분석 통계</h2>
          <div className="flex flex-col justify-between flex-1 gap-4">
            <div className="bg-gray-50 p-4 rounded-xl border border-gray-100 flex justify-between items-center">
              <div>
                <span className="text-xs text-gray-400 block font-medium">종합 뉴스 감성 지수</span>
                <span className="text-4xl font-black text-gray-800 tracking-tight mt-1 block">
                  {sentimentScore}<span className="text-lg font-bold text-gray-400"> / 100 pt</span>
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-gray-400 block font-bold">집계 방식</span>
                <span className="text-[11px] bg-slate-200 text-slate-800 font-bold px-2 py-0.5 rounded mt-1 inline-block">중립 노이즈 제거</span>
              </div>
            </div>
            <div className={`p-4 rounded-xl border border-gray-100/70 flex-1 flex flex-col justify-center ${marketReport.bg}`}>
              <div className="flex items-center gap-1.5">
                <span className="text-xs">🎯</span>
                <span className={`text-sm font-black ${marketReport.color}`}>{marketReport.status}</span>
              </div>
              <p className="text-[11px] text-gray-600 mt-1.5 leading-relaxed font-medium">{marketReport.desc}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex flex-col justify-between">
          <h2 className="text-sm font-bold text-gray-700 mb-4">실시간 거시 지표 가드</h2>
          <div className="grid grid-cols-2 gap-3 flex-1 content-center">
            <div className="p-3 bg-gray-50/60 border border-gray-100 rounded-xl">
              <span className="text-[11px] text-gray-400 block">VIX 변동성 지수</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-lg font-bold text-gray-800">{macroData?.vix_score}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-bold">{macroData?.vix_status}</span>
              </div>
            </div>
            <div className="p-3 bg-gray-50/60 border border-gray-100 rounded-xl">
              <span className="text-[11px] text-gray-400 block">원/달러 환율</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-lg font-bold text-gray-800">₩{macroData?.usd_krw_rate}</span>
                <span className="text-[9px] text-red-500 font-bold">▲ {macroData?.usd_krw_change}%</span>
              </div>
            </div>
            <div className="p-3 bg-gray-50/60 border border-gray-100 rounded-xl col-span-2">
              <span className="text-[11px] text-gray-400 block">KOSPI 지수</span>
              <div className="flex justify-between items-baseline mt-1">
                <span className="text-lg font-bold text-gray-800">{macroData?.kospi_index}</span>
                <span className="text-xs text-blue-500 font-bold">▼ {macroData?.kospi_change}%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm flex flex-col">
          <h2 className="text-sm font-bold text-gray-700 mb-3">AI 마켓 이상 징후 레이더</h2>
          <div className="flex flex-col gap-2 overflow-y-auto flex-1 max-h-[160px] pr-1">
            {anomalies.map((signal) => (
              <div key={signal.id} className={`p-2.5 rounded-xl border text-xs flex gap-2 items-start ${signal.level === 'danger' ? 'bg-red-50/60 border-red-100 text-red-950' : signal.level === 'warning' ? 'bg-amber-50/60 border-amber-100 text-amber-950' : 'bg-blue-50/60 border-blue-100 text-blue-950'}`}>
                <span className="mt-0.5">{signal.level === 'danger' ? '🚨' : signal.level === 'warning' ? '⚠️' : 'ℹ️'}</span>
                <div>
                  <div className="font-bold">{signal.title}</div>
                  <div className="text-[11px] text-gray-600 mt-0.5 leading-relaxed font-medium">{signal.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
        <div className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm md:col-span-1">
          <h2 className="text-sm font-bold text-gray-700 mb-4">📅 핵심 증시 일정 & D-Day</h2>
          <div className="flex flex-col gap-2">
            {schedules.map((schedule) => (
              <div key={schedule.id} className="flex justify-between items-center bg-gray-50 p-3 rounded-xl border border-gray-100">
                <div>
                  <span className="text-[9px] font-bold px-1.5 py-0.5 bg-gray-200 text-gray-700 rounded">
                    {schedule.category}
                  </span>
                  <div className="text-xs font-bold text-gray-800 mt-1">{schedule.title}</div>
                  <div className="text-[10px] text-gray-400 mt-0.5">{schedule.event_date}</div>
                </div>
                <span className={`text-[11px] font-black px-2.5 py-1 rounded-md ${
                  schedule.d_day === 0 ? 'bg-red-500 text-white' : 
                  schedule.d_day <= 3 ? 'bg-amber-500 text-white' : 'bg-gray-700 text-white'
                }`}>
                  {schedule.d_day === 0 ? 'D-Day' : `D-${schedule.d_day}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard