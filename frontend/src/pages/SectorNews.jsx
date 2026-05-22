import { useState, useEffect } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { newsApi } from '../api/newsApi'
import NewsCard from '../components/NewsCard'
import CommentList from '../components/CommentList'
import CommentForm from '../components/CommentForm'
import api from '../api/axios'

const PAGE_SIZE = 10

function SectorNews() {
  const { sectorId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [news, setNews] = useState([])
  const [sector, setSector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedNews, setSelectedNews] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    setCurrentPage(1)
  }, [sectorId])

  useEffect(() => {
    loadNewsAndCheckFocus(currentPage)
    loadSectorInfo()
  }, [sectorId, currentPage, location.search])

  const loadNewsAndCheckFocus = async (page) => {
    try {
      const response = await newsApi.getNewsBySector(sectorId, page, PAGE_SIZE)
      const newsItems = response.data.items
      setNews(newsItems)
      setTotalCount(response.data.total)

      // 대시보드에서 쿼리스트링(?newsId=값)을 달고 진입했을 때 강제 팝업 바인딩
      const searchParams = new URLSearchParams(location.search)
      const focusNewsId = searchParams.get('newsId') || location.state?.targetNewsId
      if (focusNewsId) {
        // 이미 받아온 뉴스 풀에서 찾거나, 없으면 단일 상세조회 API 연동 대응
        const found = newsItems.find(item => item.id === parseInt(focusNewsId))
        if (found) {
          setSelectedNews(found)
        } else {
          try {
            const singleRes = await api.get(`/news/${focusNewsId}`)
            setSelectedNews(singleRes.data)
          } catch (e) {
            console.error('단일 상세 타겟 뉴스 로드 실패:', e)
          }
        }
      }
    } catch (error) {
      console.error('뉴스 로딩 실패:', error)
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

  const handleBackToList = () => {
    setSelectedNews(null)
    navigate(`/sector/${sectorId}/news`) // 쿼리스트링 클리어 처리
  }

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

  // 뉴스 상세보기 + 댓글 (보라색 AI 분석 버튼 완벽 도려냄)
  if (selectedNews) {
    return (
      <div>
        <button
          onClick={handleBackToList}
          className="mb-6 text-blue-600 hover:text-blue-800 font-medium"
        >
          ← 목록으로 돌아가기
        </button>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <h1 className="text-2xl font-bold flex-1">{selectedNews.title}</h1>
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
              <a 
                href={selectedNews.url} 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-blue-600 hover:underline"
              >
                원문 보기 →
              </a>
            )}
          </div>
        </div>

        <CommentForm 
          newsId={selectedNews.id} 
          onCommentAdded={() => setSelectedNews({...selectedNews})}
        />

        <CommentList key={selectedNews.id} newsId={selectedNews.id} />
      </div>
    )
  }

  // 뉴스 목록
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
            {sector?.icon} {sector?.name} 뉴스
          </h1>
        </div>
        <button
          onClick={handleCollectNews}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          뉴스 수집
        </button>
      </div>

      {news.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          아직 뉴스가 없습니다. 뉴스 수집 버튼을 눌러주세요.
        </div>
      ) : (
        <>
          <div className="text-sm text-gray-500 mb-4">총 {totalCount}개</div>

          <div className="space-y-4">
            {news.map(item => (
              <div key={item.id} onClick={() => handleNewsClick(item)} className="cursor-pointer">
                <NewsCard news={item} />
              </div>
            ))}
          </div>

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
        </>
      )}
    </div>
  )
}

export default SectorNews
