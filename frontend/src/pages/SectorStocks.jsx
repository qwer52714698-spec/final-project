import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { stocksApi } from '../api/stocksApi'
import { newsApi } from '../api/newsApi'
import StockChart from '../components/StockChart'
import NewsCard from '../components/NewsCard'
import CommentList from '../components/CommentList'
import CommentForm from '../components/CommentForm'
import axios from 'axios'

function SectorStocks() {
  const { sectorId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  
  const [stocksWithPrices, setStocksWithPrices] = useState([])
  const [sector, setSector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)
  const [selectedStockCombo, setSelectedStockCombo] = useState(null)

  // 뉴스 관련 상태 관리
  const [news, setNews] = useState([])
  const [newsLoading, setNewsLoading] = useState(true)
  const [selectedNews, setSelectedNews] = useState(null)
  const [activeNewsTab, setActiveNewsTab] = useState('전체')
  const [newsPage, setNewsPage] = useState(1)
  const newsPerPage = 6

  // 🛠️ 판단 기준 툴팁 서브 토글 상태
  const [showCriteriaHelp, setShowCriteriaHelp] = useState(false)

  useEffect(() => {
    loadStocks()
    loadSectorInfo()
    loadNewsAndCheckFocus()
  }, [sectorId, days, location.search])

  const loadStocks = async () => {
    try {
      const response = await stocksApi.getSectorStocksWithPrices(sectorId, days)
      const data = response.data || []
      
      // 주가 데이터(prices)가 있는 정상 종목만 필터링하여 화면 무결성 마진 확보
      const validStocks = data.filter(item => item.prices && item.prices.length > 0)
      setStocksWithPrices(validStocks)
      
      if (validStocks.length > 0 && !selectedStockCombo) {
        setSelectedStockCombo(validStocks[0])
      }
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

  const loadNewsAndCheckFocus = async () => {
    setNewsLoading(true)
    try {
      const response = await newsApi.getNewsBySector(sectorId, 1, 50)
      const newsItems = response.data.items || []
      setNews(newsItems)

      const searchParams = new URLSearchParams(location.search)
      const focusNewsId = searchParams.get('newsId')
      if (focusNewsId) {
        const found = newsItems.find(item => item.id === parseInt(focusNewsId))
        if (found) {
          setSelectedNews(found)
        } else {
          try {
            const singleRes = await axios.get(`http://localhost:8000/news/${focusNewsId}`)
            setSelectedNews(singleRes.data)
          } catch (e) {
            console.error('단일 상세 타겟 뉴스 로드 실패:', e)
          }
        }
      }
    } catch (error) {
      console.error('뉴스 로딩 실패:', error)
    } finally {
      setNewsLoading(false)
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

  const handleCollectNews = async () => {
    try {
      await newsApi.collectNews(sectorId)
      alert('뉴스 수집을 시작했습니다. 잠시 후 새로고침 해주세요.')
    } catch (error) {
      console.error('뉴스 수집 실패:', error)
      alert('뉴스 수집에 실패했습니다.')
    }
  }

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem)
  }
const filteredNews = news.filter(n => {
    if (activeNewsTab === '전체') return true;
const sentimentMap = { '긍정': 'positive', '부정': 'negative', '중립': 'neutral' };
    return n.sentiment_label === sentimentMap[activeNewsTab];
  });
  
  const currentNews = filteredNews.slice((newsPage - 1) * newsPerPage, newsPage * newsPerPage);
  const totalPages = Math.ceil(filteredNews.length / newsPerPage);
  const handleBackToList = () => {
    setSelectedNews(null)
    navigate(`/sector/${sectorId}/stocks`)
  }

  if (loading) {
    return <div className="text-center py-20 text-xs font-bold text-gray-400">로딩 중...</div>
  }

  return (
    <div className="space-y-6 container mx-auto px-4 py-6 max-w-7xl">
      {/* 1. 컨트롤 탑 인포 헤더 상단부 */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-xs font-bold text-gray-600 hover:text-gray-900 border border-gray-200 bg-white px-3 py-1.5 rounded-xl transition shadow-sm"
          >
            돌아가기
          </button>
          <h1 className="text-2xl font-black text-gray-950 tracking-tight">
            {sector?.name} 주식 및 마켓 관제 통계
          </h1>
        </div>
        <div className="flex gap-2">
          <select 
            value={days} 
            onChange={(e) => setDays(Number(e.target.value))}
            className="border border-gray-300 rounded-xl px-3 py-1.5 bg-white text-xs font-bold text-gray-700 shadow-sm"
          >
            <option value={7}>7일</option>
            <option value={30}>30일</option>
            <option value={90}>90일</option>
          </select>
          <button
            onClick={handleCollectPrices}
            className="bg-green-600 text-white px-4 py-1.5 text-xs font-bold rounded-xl hover:bg-green-700 transition shadow-sm"
          >
            주가 수집
          </button>
          <button
            onClick={handleCollectNews}
            className="bg-blue-600 text-white px-4 py-1.5 text-xs font-bold rounded-xl hover:bg-blue-700 transition shadow-sm"
          >
            뉴스 수집
          </button>
        </div>
      </div>

      {/* 🛠️ [복구 완결] 지표 분류 가이드 및 예측 판단 기준 목록 피드백 라인 */}
      <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 shadow-sm space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-black text-gray-900">시장 예측 지표 분류</span>
          <button 
            onClick={() => setShowCriteriaHelp(!showCriteriaHelp)}
            className="w-5 h-5 flex items-center justify-center bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-bold rounded-full transition shadow-xs focus:outline-none"
            title="예측 판단 기준 보기"
          >
            ?
          </button>
        </div>
        
        {/* 토글 활성화 시 전개되는 세부 판단 가이드 목록 */}
        {showCriteriaHelp && (
          <div className="bg-white border border-gray-100 rounded-xl p-3.5 space-y-2 text-[11px] text-gray-600 leading-relaxed font-semibold shadow-inner animate-fade-in">
            <div className="text-xs font-black text-gray-800 border-b pb-1">AI 모델의 주가 트렌드 예측 판단 원칙</div>
            <ul className="list-disc list-inside space-y-1 pl-1">
              <li>긍정 파트: 수집된 실시간 뉴스 감성 분석 피드가 0.6점 이상이며 당일 종가 매수세가 우위인 종목</li>
              <li>부정 파트: 수집된 실시간 뉴스 감성 분석 피드가 -0.6점 이하이며 하방 거래량 압력이 가중된 종목</li>
              <li>중립 파트: 주요 거시 경제 지표 보합세 및 변동성 지표가 가이드 마진 내부에서 횡보하는 종목</li>
            </ul>
          </div>
        )}
      </div>

      {stocksWithPrices.length === 0 ? (
        <div className="text-center py-20 text-xs font-bold text-gray-400 bg-gray-50 rounded-2xl border border-dashed">
          주식 데이터가 없습니다. 주가 수집 버튼을 눌러주세요.
        </div>
      ) : (
        <div className="space-y-8">
          {/* 2. 주식 종목 원클릭 셀렉트 활성 탭 파트 */}
          <div className="flex flex-wrap gap-2 bg-gray-50 border border-gray-200 rounded-2xl p-2.5 shadow-sm max-h-[160px] overflow-y-auto">
            {stocksWithPrices.map((combo) => {
              const isSelected = selectedStockCombo?.stock.id === combo.stock.id
              return (
                <button
                  key={combo.stock.id}
                  onClick={() => setSelectedStockCombo(combo)}
                  className={`px-3 py-1.5 text-xs font-bold rounded-xl transition shadow-sm ${
                    isSelected
                      ? 'bg-blue-600 text-white border border-blue-600'
                      : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {combo.stock.name || `종목_${combo.stock.symbol}`} ({combo.stock.symbol})
                </button>
              )
            })}
          </div>

          {/* 3. 메인 분석 엔진 차트 컴포넌트 출력 */}
          {selectedStockCombo && selectedStockCombo.prices && selectedStockCombo.prices.length > 0 && (
            <div className="border-b pb-6">
              <StockChart stock={selectedStockCombo.stock} prices={selectedStockCombo.prices} />
            </div>
          )}

          {/* 4. 하단에 완벽하게 일체형으로 조립된 섹터 뉴스 관제 세그먼트 */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            {selectedNews ? (
              <div className="space-y-4 animate-fade-in">
                <button
                  onClick={handleBackToList}
                  className="text-xs font-bold text-blue-600 hover:text-blue-800 transition"
                >
                  목록으로 돌아가기
                </button>

                <div className="bg-gray-50 border border-gray-100 rounded-xl p-6">
                  <h2 className="text-xl font-black text-gray-900 mb-3">{selectedNews.title}</h2>
                  <div className="flex gap-2 mb-4">
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
                      selectedNews.sentiment_label === 'positive' ? 'bg-green-50 text-green-700' :
                      selectedNews.sentiment_label === 'negative' ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {selectedNews.sentiment_label === 'positive' ? '긍정' :
                       selectedNews.sentiment_label === 'negative' ? '부정' : '중립'}
                      {' '}{selectedNews.sentiment_score?.toFixed(2)}
                    </span>
                  </div>

                  {selectedNews.ai_summary && (
                    <div className="bg-blue-50/60 border border-blue-100 p-4 rounded-xl mb-4 text-xs">
                      <h4 className="font-black text-blue-900 mb-1">AI 요약 브리핑</h4>
                      <p className="text-gray-700 leading-relaxed">{selectedNews.ai_summary}</p>
                    </div>
                  )}

                  {selectedNews.content && (
                    <div className="text-xs text-gray-600 leading-relaxed font-medium whitespace-pre-wrap mb-4">
                      {selectedNews.content}
                    </div>
                  )}

                  <div className="flex justify-between items-center text-[10px] text-gray-400 border-t pt-3 font-semibold">
                    <span>수집 시각: {new Date(selectedNews.published_at).toLocaleDateString('ko-KR')}</span>
                    {selectedNews.url && (
                      <a href={selectedNews.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        네이버 원문 뉴스 보기
                      </a>
                    )}
                  </div>
                </div>

                <CommentForm newsId={selectedNews.id} onCommentAdded={() => setSelectedNews({...selectedNews})} />
                <CommentList key={selectedNews.id} newsId={selectedNews.id} />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="border-b pb-2">
                  <h3 className="text-base font-black text-gray-900">{sector?.name || '섹터'} 관련 실시간 마켓 소식 피드</h3>
                </div>

                {newsLoading ? (
                  <div className="text-center py-12 text-xs text-gray-400 font-bold animate-pulse">실시간 기사를 파싱해오는 중입니다.</div>
                ) : news.length === 0 ? (
                  <div className="text-center py-12 text-xs font-bold text-gray-400 bg-gray-50 rounded-xl border border-dashed">
                    아직 수집된 기사가 존재하지 않습니다.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* 탭 버튼 */}
                    <div className="flex gap-2 mb-4">
                      {['전체', '긍정', '부정', '중립'].map(tab => (
                        <button key={tab} onClick={() => { setActiveNewsTab(tab); setNewsPage(1); }} className={`px-4 py-1 text-xs font-bold rounded-full border ${activeNewsTab === tab ? 'bg-slate-800 text-white' : 'bg-gray-100'}`}>
                          {tab}
                        </button>
                      ))}
                    </div>
                    {/* 뉴스 목록 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 min-h-[300px]">
                      {currentNews.map(item => (
                        <div key={item.id} onClick={() => handleNewsClick(item)} className="cursor-pointer transition transform hover:-translate-y-0.5">
                          <NewsCard news={item} />
                        </div>
                      ))}
                    </div>
                    {/* 페이지네이션 */}
                    <div className="flex justify-center gap-2 mt-6">
                      {[...Array(totalPages)].map((_, i) => (
                        <button key={i} onClick={() => setNewsPage(i + 1)} className={`px-3 py-1 text-xs font-bold rounded ${newsPage === i + 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                          {i + 1}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SectorStocks