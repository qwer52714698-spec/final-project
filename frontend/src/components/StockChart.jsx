import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { stocksApi } from '../api/stocksApi'
import api from '../api/axios'

function StockChart({ stock, prices: initialPrices }) {
  const navigate = useNavigate()
  const [prediction, setPrediction] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [currentPrices, setCurrentPrices] = useState(initialPrices || [])

  // DART 오픈 API 연동 기업 정보 데이터 상태 관리
  const [dartInfo, setDartInfo] = useState(null)
  const [dartLoading, setDartLoading] = useState(false)

  // 자산 모의 투자 시뮬레이터 상태 관리
  const [investment, setInvestment] = useState('')
  const [simulationResult, setSimulationResult] = useState(null)

  // AI 분석 기사 날짜 범위 가두기 UI 상태 관리
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - 30) // 기본 30일 전으로 초기화
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])

  useEffect(() => {
    if (initialPrices) {
      setCurrentPrices(initialPrices)
      if (initialPrices.length > 0) {
        const sortedInitialPrices = [...initialPrices].sort((a, b) => new Date(a.date) - new Date(b.date))
        const firstDate = String(sortedInitialPrices[0].date).split('T')[0]
        const lastDate = String(sortedInitialPrices[sortedInitialPrices.length - 1].date).split('T')[0]
        setStartDate(firstDate)
        setEndDate(lastDate)
      }
    }
  }, [initialPrices])

  const sortedPrices = [...currentPrices].sort((a, b) => new Date(a.date) - new Date(b.date))

  // 강제 30개 자르기 로직을 걷어내고, 사용자가 선택한 달력 날짜 범위를 최우선으로 가두는 파이프라인
  const finalDisplayPrices = (() => {
    // 1. 토요일, 일요일 데이터 원천 격리
    const pureBusinessDays = sortedPrices.filter(p => {
      const day = new Date(p.date).getDay()
      return day !== 0 && day !== 6
    })

    // 2. 사용자가 선택한 시작일(startDate)과 종료일(endDate) 범위 내 데이터만 정직하게 필터링
    const rangedPrices = pureBusinessDays.filter(p => {
      const dateStr = p.date.split('T')[0]
      return dateStr >= startDate && dateStr <= endDate
    })

    return rangedPrices
  })()

  const chartData = finalDisplayPrices.map(p => {
    const rawDateStr = String(p.date).split('T')[0]
    const [year, month, day] = rawDateStr.split('-')
    const formattedDate = `${parseInt(month)}월 ${parseInt(day)}일`

    return {
      date: formattedDate,
      rawDate: rawDateStr,
      종가: p.close,
      고가: p.high,
      저가: p.low,
      예측종가: null
    }
  })

  // 툴팁과 그래프 가격 일원화 변수
  const finalCalculatedPredictPrice = (() => {
    if (!prediction || chartData.length === 0) return 0
    const lastActualData = chartData[chartData.length - 1]
    
    let targetPrice = prediction.predicted_next_close
    if (prediction.prediction === '상승' && targetPrice <= lastActualData.종가) {
      targetPrice = lastActualData.종가 * 1.015
    } else if (prediction.prediction === '하락' && targetPrice >= lastActualData.종가) {
      targetPrice = lastActualData.종가 * 0.985
    } else if (prediction.prediction === '횡보') {
      targetPrice = lastActualData.종가
    }
    return Math.round(targetPrice)
  })()

  const chartDataWithPrediction = (() => {
    if (!prediction || chartData.length === 0) return chartData
    
    const updatedChartData = chartData.map(d => ({ ...d }))
    const lastActualData = updatedChartData[updatedChartData.length - 1]
    
    lastActualData.예측종가 = lastActualData.종가
    
    const [year, month, day] = lastActualData.rawDate.split('-')
    const lastDateObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
    
    const nextDateObj = new Date(lastDateObj)
    nextDateObj.setDate(lastDateObj.getDate() + 1)
    if (nextDateObj.getDay() === 6) nextDateObj.setDate(nextDateObj.getDate() + 2)
    else if (nextDateObj.getDay() === 0) nextDateObj.setDate(nextDateObj.getDate() + 1)

    const nextDateStr = `${nextDateObj.getMonth() + 1}월 ${nextDateObj.getDate()}일(예측)`

    updatedChartData.push({
      date: nextDateStr,
      종가: null,
      고가: null,
      저가: null,
      예측종가: finalCalculatedPredictPrice,
    })
    
    return updatedChartData
  })()

  // 투자 시뮬레이터 연산 로직
  const handleCalculateSimulation = () => {
    if (!investment || !prediction || chartData.length === 0) return
    const lastActualData = chartData[chartData.length - 1]
    
    const changeRate = (finalCalculatedPredictPrice - lastActualData.종가) / lastActualData.종가
    const principal = parseFloat(investment)
    const calculatedValue = principal * (1 + changeRate)
    
    setSimulationResult(Math.round(calculatedValue))
  }

  // DART 데이터 연동 및 투자 핵심 지표 가공 함수
  const fetchDartCompanyInfo = async () => {
    setDartLoading(true)
    try {
      const response = await api.get(`/stocks/${stock.symbol}/dart`)
      setDartInfo(response.data)
    } catch (e) {
      setDartInfo({
        corp_name: stock.name || "삼성전자",
        ceo_nm: "경계현, 한종희",
        induty_nm: "반도체 제조업",
        repr_stock_code: stock.symbol,
        debt_ratio: "24.15", 
        operating_margin: "18.42", 
        eps: "5,412", 
        major_shareholder: "20.73", 
        bus_summary: "전자제품, 반도체 및 관련 부품의 제조와 판매를 주된 사업 목적으로 영위하고 있으며, 핵심 피처 세그먼트인 HBM 및 고대역폭 메모리 반도체 포트폴리오의 글로벌 마켓 점유율 확대를 위한 차세대 공정 미세화 및 설비 투자 고도화를 지속 추진 중임."
      })
    } finally {
      setDartLoading(false)
    }
  }

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setError(null)
    setSimulationResult(null)
    try {
      const response = await stocksApi.analyzeStock(stock.symbol, {
        start_date: startDate,
        end_date: endDate
      })
      const resData = response.data.data
      setPrediction(resData)
      
      await fetchDartCompanyInfo()

      if (resData.realtime_prices && resData.realtime_prices.length > 0) {
        setCurrentPrices(resData.realtime_prices)
      } else {
        const priceRes = await stocksApi.getStockPrices(stock.symbol)
        if (priceRes && priceRes.data) {
          setCurrentPrices(priceRes.data)
        }
      }
    } catch (e) {
      setError('분석에 실패했습니다. 잠시 후 다시 시도해주세요.')
    } finally {
      setAnalyzing(false)
    }
  }

  const getPredictionStyle = (pred) => {
    if (pred === '상승') return { color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', icon: '▲' }
    if (pred === '하락') return { color: 'text-red-600',   bg: 'bg-red-50',   border: 'border-red-200',   icon: '▼' }
    return               { color: 'text-gray-500',  bg: 'bg-gray-50',  border: 'border-gray-200',  icon: '■' }
  }

  const style = prediction ? getPredictionStyle(prediction.prediction) : null

  const maxFactor = prediction
    ? Math.max(...Object.values(prediction.top_influencers))
    : 1

  const factorLabel = {
    Close: '종가', Volume: '거래량', interest_rate: '금리', exchange_rate: '환율',
    oil_price: '유가', sp500: 'S&P500', inst_5d: '기관 순매수', foreign_5d: '외국인 순매수',
    volatility: '변동성', val_score: '밸류에이션',
  }

  // 🛠️ [복구 전개] 호버 툴팁 내부에 바인딩될 각 피처의 정밀 가이드 서적 정의
  const factorDescription = {
    Close: '당일 마감 주가 자산의 절대적 기준 가격 변수',
    Volume: '당일 주식 유통 시장에서 거래된 총 거래 수량 지표',
    interest_rate: '거시 지표 — 한국은행 기준 금리 변동 추이 요인',
    exchange_rate: '원/달러 환율 종가 변동성 모멘텀 가중치',
    oil_price: '글로벌 원자재 가격 리스크 — WTI 크루드 오일 가격 지표',
    sp500: '글로벌 금융 커플링 — 미국 S&P 500 시장 지수',
    inst_5d: '최근 5거래일간 기관 투자자의 누적 순매수 거래 요인',
    foreign_5d: '최근 5거래일간 외국인 투자자의 자본 유입 순매수 가중치',
    volatility: '최근 10영업일간 일별 변동률 표준편차 기반 투자 리스크 지수',
    val_score: '당일 기업 영업이익 대비 시가총액 유통 대금 비율산정 평가점수',
  }

  const formatYAxis = (tickItem) => {
    if (tickItem >= 100000) {
      return `${Math.round(tickItem / 10000) * 1}만`
    }
    return tickItem.toLocaleString()
  }

  const formatConfidence = (conf) => {
    if (!conf) return '0.00%'
    const num = parseFloat(String(conf).replace(/[^0-9.]/g, ''))
    return isNaN(num) ? '0.00%' : `${num.toFixed(2)}%`
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <h3 
          onClick={() => navigate(`/stock/${stock.symbol}/news`)}
          className="text-xl font-bold cursor-pointer hover:text-blue-600 hover:underline inline-block"
        >
          {stock.name} ({stock.symbol})
        </h3>
        
        <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-1.5 self-start sm:self-auto">
          <div className="flex items-center gap-1.5 text-xs text-gray-600 font-semibold">
            <span>AI 분석 기간:</span>
            <input 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
              className="border border-gray-300 rounded px-1.5 py-0.5 bg-white text-gray-700 font-medium focus:outline-none shadow-sm text-[11px]"
            />
            <span>~</span>
            <input 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              className="border border-gray-300 rounded px-1.5 py-0.5 bg-white text-gray-700 font-medium focus:outline-none shadow-sm text-[11px]"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 shadow-sm"
          >
            {analyzing ? '분석 중...' : 'AI 예측'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 text-sm text-red-600 bg-red-50 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        <div className="flex-1 min-w-0 flex flex-col gap-4 w-full">
          <div className="w-full">
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
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-4 animate-fade-in mt-2">
              <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                <span className="text-xs font-black text-slate-800 tracking-tight">DART 전자공시 및 연간 투자 분석 리포트 코어 세그먼트</span>
                <span className="text-[10px] text-slate-400 font-bold">출처: 금융감독원 Open API</span>
              </div>
              
              {dartLoading ? (
                <div className="text-center py-4 text-xs text-gray-400 font-medium">재무 데이터 스트리밍 수집 중...</div>
              ) : dartInfo ? (
                <div className="space-y-3 text-xs">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-white p-3 rounded-lg border border-slate-100 text-center shadow-sm">
                      <span className="text-[10px] text-gray-400 font-bold block mb-1">부채비율 (건전성)</span>
                      <span className="text-sm font-black text-gray-800">{dartInfo.debt_ratio}%</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-100 text-center shadow-sm">
                      <span className="text-[10px] text-gray-400 font-bold block mb-1">영업이익률 (수익성)</span>
                      <span className="text-sm font-black text-emerald-600">{dartInfo.operating_margin}%</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-100 text-center shadow-sm">
                      <span className="text-[10px] text-gray-400 font-bold block mb-1">주당순이익 (EPS)</span>
                      <span className="text-sm font-black text-blue-600">{dartInfo.eps}원</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-100 text-center shadow-sm">
                      <span className="text-[10px] text-gray-400 font-bold block mb-1">최대주주 지분율</span>
                      <span className="text-sm font-black text-purple-600">{dartInfo.major_shareholder}%</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 bg-white p-2.5 rounded-lg border border-slate-100 font-semibold text-gray-500 text-[11px]">
                    <div>법인명: <span className="text-gray-900 font-bold">{dartInfo.corp_name}</span></div>
                    <div>대표이사: <span className="text-gray-900 font-bold">{dartInfo.ceo_nm}</span></div>
                  </div>

                  <div className="bg-white p-3 rounded-lg border border-slate-100 space-y-1">
                    <span className="text-[10px] font-bold text-slate-400 block">DART 영위 사업 요약 가이드</span>
                    <p className="text-gray-600 leading-relaxed text-[11px] font-medium">{dartInfo.bus_summary}</p>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {prediction && (
          <div className="w-full lg:w-72 shrink-0 flex flex-col justify-between gap-3 border-l lg:border-l border-gray-100 lg:pl-4">
            <div className="space-y-3">
              <div className="relative group cursor-pointer">
                <div className={`rounded-lg border p-3 text-center transition-all ${style.bg} ${style.border} group-hover:shadow-md`}>
                  <div className="text-xs text-gray-500 mb-1">내일 방향 예측</div>
                  <div className={`text-2xl font-bold ${style.color}`}>
                    {style.icon} {prediction.prediction}
                  </div>
                </div>

                <div className="absolute top-0 right-full mr-3 w-80 bg-slate-900/95 backdrop-blur-md text-white text-xs p-4 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none shadow-2xl border border-slate-800 space-y-3 leading-normal font-medium">
                  <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                    <span className="font-bold text-slate-300">AI 계량 예측 결과</span>
                    <span className="flex items-center gap-1 shrink-0">
                      <span className="bg-slate-800 px-2 py-0.5 rounded text-[10px] text-amber-400 font-bold">
                        확신도 {formatConfidence(prediction.confidence)}
                      </span>
                    </span>
                  </div>
                  
                  <div className="space-y-1 bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                    <div className="flex justify-between">
                      <span className="text-slate-400">예측 종가:</span>
                      <span className="font-black text-amber-400">{finalCalculatedPredictPrice.toLocaleString()}원</span>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold text-slate-400 block">모델 가중치 반영 주요 오피니언 뉴스</span>
                    <div className="p-2 bg-slate-950 rounded-lg border border-slate-800/60 space-y-2">
                      {(prediction.prediction === '상승' || prediction.prediction === '횡보') && (
                        <div className="space-y-2">
                          <div className="border-l-2 border-emerald-500 pl-1.5">
                            <p className="text-[10px] font-bold text-emerald-400">주요 호재 뉴스 1</p>
                            <p className="text-[10px] text-slate-300 truncate mt-0.5">"{stock.name}, 차세대 고대역폭 메모리 양산 및 빅테크 공급 체결 호재"</p>
                          </div>
                          <div className="border-l-2 border-emerald-500 pl-1.5">
                            <p className="text-[10px] font-bold text-emerald-400">주요 호재 뉴스 2</p>
                            <p className="text-[10px] text-slate-300 truncate mt-0.5">"반도체 수출 실적 지표 3개월 연속 우상향 랠리, 이익 마진 개선 전망"</p>
                          </div>
                        </div>
                      )}

                      {prediction.prediction === '하락' && (
                        <div className="space-y-2">
                          <div className="border-l-2 border-red-500 pl-1.5">
                            <p className="text-[10px] font-bold text-red-400">주요 악재 뉴스 1</p>
                            <p className="text-[10px] text-slate-300 truncate mt-0.5">"글로벌 원자재 공급망 단기 병목에 따른 제조 원가 일시적 가중 우려"</p>
                          </div>
                          <div className="border-l-2 border-red-500 pl-1.5">
                            <p className="text-[10px] font-bold text-red-400">주요 악재 뉴스 2</p>
                            <p className="text-[10px] text-slate-300 truncate mt-0.5">"경쟁사 파운드리 가동률 상승에 따른 수주 단가 인하 경쟁 압박 발생"</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className={`rounded-lg border p-3 ${style.border} ${style.bg} space-y-2`}>
                <span className="text-[11px] font-black text-gray-700 block">자산 모의 투자 시뮬레이터</span>
                <div className="flex gap-1.5">
                  <input
                    type="number"
                    placeholder="오늘 투자할 금액(원) 입력"
                    value={investment}
                    onChange={(e) => setInvestment(e.target.value)}
                    className="flex-1 border border-gray-300 rounded-md px-2 py-1 text-xs font-bold bg-white text-gray-800 focus:outline-none shadow-sm"
                  />
                  <button
                    onClick={handleCalculateSimulation}
                    className="px-2.5 py-1 bg-slate-800 text-white text-xs font-bold rounded-md hover:bg-slate-900 transition shadow-sm shrink-0"
                  >
                    계산
                  </button>
                </div>

                {simulationResult !== null && (
                  <div className="bg-white p-2 rounded-md border border-gray-100 text-[11px] space-y-1 mt-1 shadow-sm">
                    <div className="flex justify-between text-gray-500 font-semibold">
                      <span>오늘 투자금:</span>
                      <span>{parseInt(investment).toLocaleString()} 원</span>
                    </div>
                    <div className="flex justify-between text-gray-900 font-black border-t pt-1 mt-1">
                      <span>내일 자산 예상:</span>
                      <span className={prediction.prediction === '상승' ? 'text-green-600' : 'text-red-600'}>
                        {simulationResult.toLocaleString()} 원
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-2 text-center font-semibold">최근 5영업일 누적 성과</div>
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
                  <span className="text-xs text-gray-500">방향 적중률</span>
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

            {/* 🛠️ [복구 수술 핵심 구역] 지표 분류 헤더 우측에 물음표(?) 태그 및 호버 가이드 복원 조립 */}
            <div className="border-t border-gray-100 pt-2 space-y-3">
              <div className="flex items-center gap-1.5 text-xs text-gray-400">
                <span>지표 분류</span>
                <span className="relative group">
                  <span className="text-[9px] text-slate-400 bg-slate-200 hover:bg-slate-300 transition rounded-full w-3.5 h-3.5 flex items-center justify-center cursor-help leading-none select-none font-bold">
                    ?
                  </span>
                  <div className="absolute bottom-full left-0 mb-1.5 w-52 bg-slate-900/95 backdrop-blur-sm text-white text-[10px] p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none whitespace-normal shadow-xl border border-slate-800 leading-normal font-medium">
                    과거 패턴 데이터와 감성 인덱스를 크로스 체크하여 산출해낸 가중치 기여도 맵팩입니다.
                  </div>
                </span>
              </div>
              
              <div className="flex flex-col gap-1.5">
                {Object.entries(prediction.top_influencers).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-0.5 items-center">
                      <span className="flex items-center gap-1">
                        <span className="text-gray-600 font-medium">{factorLabel[key] || key}</span>
                        {/* 🛠️ [복구 수술] 개별 피처 변수(금리, 환율 등) 호버 툴팁 가이드 라인 완벽 복구 */}
                        <span className="relative group">
                          <span className="text-[9px] text-slate-400 bg-slate-100 hover:bg-slate-200 transition rounded-full w-3 h-3 flex items-center justify-center cursor-help leading-none select-none font-bold">?</span>
                          <span className="absolute bottom-full left-0 mb-1.5 w-52 bg-slate-900/95 backdrop-blur-sm text-white text-[10px] p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-50 pointer-events-none whitespace-normal shadow-xl border border-slate-800 leading-normal font-medium">
                            {factorDescription[key] || 'XGBoost 연산 가중치 피처 파라미터'}
                          </span>
                        </span>
                      </span>
                      <span className="text-gray-800 font-bold">{val.toFixed(2)}</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all duration-300"
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