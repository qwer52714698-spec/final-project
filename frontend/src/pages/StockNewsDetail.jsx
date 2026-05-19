import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'

function StockNewsDetail() {
  const { symbol } = useParams()
  const navigate = useNavigate()
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(true)
  
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const pageSize = 10

  useEffect(() => {
    const fetchNews = async () => {
      setLoading(true)
      try {
        const response = await newsApi.getStockNews(symbol, currentPage, pageSize)
        setNews(response.data.items)
        setTotalCount(response.data.total)
      } catch (error) {
        console.error('종목 뉴스 로딩 실패:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchNews()
  }, [symbol, currentPage])

  const totalPages = Math.ceil(totalCount / pageSize)

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber)
      window.scrollTo(0, 0)
    }
  }

  const renderPageNumbers = () => {
    const pageNumbers = []
    const maxVisiblePages = 3

    if (totalPages <= 5) {
      for (let i = 1; i <= totalPages; i++) {
        pageNumbers.push(i)
      }
    } else {
      pageNumbers.push(1)

      let start = Math.max(2, currentPage - 1)
      let end = Math.min(totalPages - 1, currentPage + 1)

      if (currentPage <= maxVisiblePages) {
        end = 4
      } else if (currentPage > totalPages - maxVisiblePages) {
        start = totalPages - 3
      }

      if (start > 2) {
        pageNumbers.push('...')
      }

      for (let i = start; i <= end; i++) {
        pageNumbers.push(i)
      }

      if (end < totalPages - 1) {
        pageNumbers.push('...')
      }

      pageNumbers.push(totalPages)
    }

    return pageNumbers.map((page, index) => {
      if (page === '...') {
        return (
          <span key={`ellipse-${index}`} className="px-2 text-gray-400 font-medium">
            ...
          </span>
        )
      }

      return (
        <button
          key={`page-${page}`}
          onClick={() => handlePageChange(page)}
          className={`px-4 py-2 border rounded-lg text-sm font-medium transition ${
            currentPage === page
              ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          {page}
        </button>
      )
    })
  }

  if (loading && news.length === 0) return <div className="text-center py-20">관련 뉴스 로딩 중...</div>

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button onClick={() => navigate(-1)} className="text-gray-600 hover:text-gray-900 mb-6 flex items-center gap-2">
        ← 이전으로 돌아가기
      </button>
      
      <h1 className="text-3xl font-bold mb-8">🔍 {symbol} 관련 주요 뉴스</h1>

      {news.length === 0 ? (
        <div className="text-center py-20 text-gray-500">해당 종목과 관련된 최신 뉴스 기사가 없습니다.</div>
      ) : (
        <>
          <div className="space-y-6 mb-10">
            {news.map((item) => (
              <div key={item.id} className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition">
                <h2 className="text-xl font-bold text-gray-900 mb-2">
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
                    {item.title}
                  </a>
                </h2>
                <p className="text-gray-600 text-sm line-clamp-3 mb-4">{item.content}</p>
                <div className="text-xs text-gray-400">발행일: {new Date(item.published_at).toLocaleString()}</div>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-8">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-600 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                이전
              </button>

              {renderPageNumbers()}

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-600 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                다음
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default StockNewsDetail