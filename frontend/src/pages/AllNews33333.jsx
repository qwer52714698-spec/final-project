import { useState, useEffect } from 'react'
import { newsApi } from '../api/newsApi'
import NewsCard from '../components/NewsCard'
import CommentList from '../components/CommentList'
import CommentForm from '../components/CommentForm'

const PAGE_SIZE = 10

function AllNews() {
  const [news, setNews] = useState([])
  const [sectors, setSectors] = useState([])
  const [selectedSector, setSelectedSector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedNews, setSelectedNews] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  // ✅ 댓글 새로고침용
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    loadSectors()
  }, [])

  useEffect(() => {
    setCurrentPage(1)
    loadNews(1)
  }, [selectedSector])

  useEffect(() => {
    loadNews(currentPage)
  }, [currentPage])

  const loadSectors = async () => {
    try {
      const response = await newsApi.getSectors()
      setSectors(response.data)
    } catch (error) {
      console.error('섹터 로딩 실패:', error)
    }
  }

  const loadNews = async (page) => {
    setLoading(true)
    try {
      const response = await newsApi.getAllNews(page, PAGE_SIZE, selectedSector)
      setNews(response.data.items)
      setTotalCount(response.data.total)
    } catch (error) {
      console.error('뉴스 로딩 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeAll = async () => {
    try {
      await newsApi.analyzeNews()
      alert('AI 감성 분석을 시작했습니다. 잠시 후 새로고침 해주세요.')
    } catch (error) {
      console.error('분석 실패:', error)
      alert('분석에 실패했습니다.')
    }
  }

  const handleAnalyzeSingle = async () => {
    if (!selectedNews) return
    setAnalyzing(true)
    try {
      const response = await newsApi.analyzeSingleNews(selectedNews.id)
      alert('AI 감성 분석이 완료되었습니다.')
      setSelectedNews(response.data)
    } catch (error) {
      console.error('분석 실패:', error)
      alert('AI 분석에 실패했습니다.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleNewsClick = (newsItem) => setSelectedNews(newsItem)
  const handleBackToList = () => setSelectedNews(null)

  const totalPages = Math.ceil(totalCount / PAGE_SIZE)

  const getPageNumbers = () => {
    const pages = []
    let start = Math.max(1, currentPage - 2)
    let end = Math.min(totalPages, start + 4)
    if (end - start < 4) start = Math.max(1, end - 4)
    for (let i = start; i <= end; i++) pages.push(i)
    return pages
  }

  if (loading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  if (selectedNews) {
    return (
      <div>
        <button onClick={handleBackToList} className="mb-6 text-blue-600 hover:text-blue-800 font-medium">
          ← 목록으로 돌아가기
        </button>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold flex-1">{selectedNews.title}</h1>
            <button
              onClick={handleAnalyzeSingle}
              disabled={analyzing}
              className="ml-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:bg-gray-400"
            >
              {analyzing ? '분석 중...' : '🤖 AI 분석'}
            </button>
          </div>

          <div className="flex gap-3 mb-4">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              selectedNews.sentiment_label === 'positive' ? 'bg-green-100 text-green-700' :
              selectedNews.sentiment_label === 'negative' ? 'bg-red-100 text-red-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {selectedNews.sentiment_label === 'positive' ? '긍정' :
               selectedNews.sentiment_label === 'negative' ? '부정' : '중립'}
              {' '}{selectedNews.sentiment_score?.toFixed(2)}
            </span>
          </div>

          {selectedNews.ai_summary && (
            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold mb-2">📝 AI 요약</h3>
              <p className="text-gray-700">{selectedNews.ai_summary}</p>
            </div>
          )}

          {selectedNews.content && (
            <div className="mb-4">
              <p className="text-gray-700 whitespace-pre-wrap">{selectedNews.content}</p>
            </div>
          )}

          <div className="flex justify-between items-center text-sm text-gray-500 border-t pt-4">
            <span>{new Date(selectedNews.published_at).toLocaleDateString('ko-KR')}</span>
            {selectedNews.url && (
              <a href={selectedNews.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                원문 보기 →
              </a>
            )}
          </div>
        </div>

        {/* ✅ 댓글 작성 후 refreshKey 증가 → CommentList 자동 새로고침 */}
        <CommentForm
          newsId={selectedNews.id}
          onCommentAdded={() => setRefreshKey(k => k + 1)}
        />

        <CommentList
          key={selectedNews.id}
          newsId={selectedNews.id}
          refresh={refreshKey}
        />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">전체 뉴스</h1>
        <button onClick={handleAnalyzeAll} className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition">
          AI 감성 분석
        </button>
      </div>

      <div className="mb-6 flex gap-2 flex-wrap">
        <button
          onClick={() => setSelectedSector(null)}
          className={`px-4 py-2 rounded-lg transition ${selectedSector === null ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
        >
          전체
        </button>
        {sectors.map(sector => (
          <button
            key={sector.id}
            onClick={() => setSelectedSector(sector.id)}
            className={`px-4 py-2 rounded-lg transition ${selectedSector === sector.id ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            {sector.icon} {sector.name}
          </button>
        ))}
      </div>

      {totalCount > 0 && (
        <div className="text-sm text-gray-500 mb-4">총 {totalCount}개</div>
      )}

      {news.length === 0 ? (
        <div className="text-center py-20 text-gray-500">뉴스가 없습니다.</div>
      ) : (
        <div className="space-y-4">
          {news.map(item => (
            <div key={item.id} onClick={() => handleNewsClick(item)} className="cursor-pointer">
              <NewsCard news={item} />
            </div>
          ))}
        </div>
      )}

      {/* ✅ 페이지네이션 */}
      {totalPages > 1 && (
        <div className="mt-8">
          <div className="flex items-center justify-center gap-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="w-9 h-9 flex items-center justify-center rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-30 transition"
            >
              ←
            </button>
            {getPageNumbers().map(page => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`w-9 h-9 flex items-center justify-center rounded-lg text-sm font-medium transition ${
                  currentPage === page
                    ? 'bg-blue-600 text-white border border-blue-600'
                    : 'border border-gray-300 text-gray-700 hover:bg-gray-100'
                }`}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="w-9 h-9 flex items-center justify-center rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-100 disabled:opacity-30 transition"
            >
              →
            </button>
          </div>
          <div className="text-center text-xs text-gray-400 mt-2">
            {currentPage} / {totalPages} 페이지 · 총 {totalCount}개
          </div>
        </div>
      )}
    </div>
  )
}

export default AllNews
