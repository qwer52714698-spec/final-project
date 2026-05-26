import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { newsApi } from '../api/newsApi'
import NewsCard from '../components/NewsCard'
import CommentList from '../components/CommentList'
import CommentForm from '../components/CommentForm'
import api from '../api/axios'

const PAGE_SIZE = 10

function AllNews() {
  const navigate = useNavigate()
  const location = useLocation()
  const [news, setNews] = useState([])
  const [sectors, setSectors] = useState([])
  const [selectedSector, setSelectedSector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedNews, setSelectedNews] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [updatedComments, setUpdatedComments] = useState(null)

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

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const focusNewsId = searchParams.get('newsId')

    if (focusNewsId) {
      if (news && news.length > 0) {
        const found = news.find(item => item.id === parseInt(focusNewsId))
        if (found) {
          setSelectedNews(found)
          return
        }
      }

      api.get(`/news/${focusNewsId}`)
        .then(res => {
          setSelectedNews(res.data)
        })
        .catch(err => {
          console.error('대시보드 타겟 뉴스 상세 데이터 조회 실패:', err)
        })
    }
  }, [news, location.search])

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

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem)
    setUpdatedComments(null)
  }

  const handleBackToList = () => {
    setSelectedNews(null)
    setUpdatedComments(null)
    navigate('/news')
  }

  const handleCommentAdded = (newCommentsList) => {
    setUpdatedComments(newCommentsList)
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

  if (loading && news.length === 0) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  if (selectedNews) {
    return (
      <div>
        <button onClick={handleBackToList} className="mb-6 text-blue-600 hover:text-blue-800 font-medium">
          목록으로 돌아가기
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
              <h3 className="font-semibold mb-2">AI 요약</h3>
              <p className="text-gray-700">{selectedNews.ai_summary}</p>
            </div>
          )}

          {selectedNews.content && (
            <div className="mb-4">
              <p className="text-gray-700 whitespace-pre-wrap">{selectedNews.content}</p>
            </div>
          )}

          <div className="flex justify-between items-center text-sm text-gray-500 border-t pt-4">
            <span>{new Date(selectedNews.published_at || selectedNews.collected_at).toLocaleDateString('ko-KR')}</span>
            {selectedNews.url && (
              <a href={selectedNews.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                원문 보기
              </a>
            )}
          </div>
        </div>

        <CommentForm newsId={selectedNews.id} onCommentAdded={handleCommentAdded} />
        <CommentList newsId={selectedNews.id} comments={updatedComments} />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">전체 뉴스 관제</h1>
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