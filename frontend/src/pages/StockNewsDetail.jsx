import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'
import { commentsApi } from '../api/commentsApi'
import CommentForm from '../components/CommentForm'
import axios from 'axios'

function StockNewsDetail() {
  const { symbol } = useParams()
  const navigate = useNavigate()
  const [news, setNews] = useState([])
  const [loading, setLoading] = useState(true)
  
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const pageSize = 10

  const [commentsMap, setCommentsMap] = useState({})
  const [openCommentsMap, setOpenCommentsMap] = useState({})
  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      try {
        const base64Url = token.split('.')[1]
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
        const payload = JSON.parse(window.atob(base64))
        setCurrentUser(payload)
      } catch (error) {
        console.error('유저 정보 디코딩 실패:', error)
      }
    }
  }, [])

  const fetchCommentsForNews = async (newsId) => {
    try {
      const response = await commentsApi.getComments(newsId)
      setCommentsMap(prev => ({
        ...prev,
        [newsId]: response.data
      }))
    } catch (error) {
      console.error(`댓글 로딩 실패 (뉴스 ID: ${newsId}):`, error)
    }
  }

  useEffect(() => {
    const fetchNewsAndComments = async () => {
      setLoading(true)
      try {
        const response = await newsApi.getStockNews(symbol, currentPage, pageSize)
        const newsItems = response.data.items
        setNews(newsItems)
        setTotalCount(response.data.total)

        if (newsItems && newsItems.length > 0) {
          newsItems.forEach(item => {
            fetchCommentsForNews(item.id)
          })
        }
      } catch (error) {
        console.error('종목 뉴스 로딩 실패:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchNewsAndComments()
  }, [symbol, currentPage])

  const handleDeleteComment = async (commentId, newsId) => {
    if (!window.confirm('댓글을 정말 삭제하시겠습니까?')) return

    try {
      const token = localStorage.getItem('token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      
      await axios.delete(`http://localhost:8000/comments/${commentId}`, { headers })
      alert('댓글이 안전하게 삭제되었습니다.')
      fetchCommentsForNews(newsId)
    } catch (error) {
      console.error('댓글 삭제 실패:', error)
      alert(error.response?.data?.detail || '댓글 삭제에 실패했습니다.')
    }
  }

  const totalPages = Math.ceil(totalCount / pageSize)

  const handlePageChange = (pageNumber) => {
    if (pageNumber >= 1 && pageNumber <= totalPages) {
      setCurrentPage(pageNumber)
      window.scrollTo(0, 0)
    }
  }

  const toggleComments = (newsId) => {
    setOpenCommentsMap(prev => ({
      ...prev,
      [newsId]: !prev[newsId]
    }))
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
          <div className="space-y-12 mb-10">
            {news.map((item) => {
              const isCommentsOpen = !!openCommentsMap[item.id]
              const commentCount = commentsMap[item.id]?.length || 0

              return (
                <div key={item.id} className="p-6 bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition">
                  <h2 className="text-xl font-bold text-gray-900 mb-2">
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:text-blue-600">
                      {item.title}
                    </a>
                  </h2>
                  <p className="text-gray-600 text-sm line-clamp-3 mb-4">{item.content}</p>
                  <div className="text-xs text-gray-400 mb-4">발행일: {new Date(item.published_at).toLocaleString()}</div>

                  <div className="flex justify-start mb-2">
                    <button
                      onClick={() => toggleComments(item.id)}
                      className="flex items-center gap-1.5 px-4 py-1.5 border border-gray-200 bg-white rounded-full text-xs font-medium text-gray-600 hover:bg-gray-50 transition shadow-sm"
                    >
                      💬 댓글 {isCommentsOpen ? '접기' : `보기 (${commentCount})`}
                    </button>
                  </div>

                  {isCommentsOpen && (
                    <div className="border-t border-gray-100 pt-6 bg-gray-50/50 -mx-6 -mb-6 p-6 rounded-b-xl mt-4">
                      <div className="mb-4 space-y-3">
                        {commentsMap[item.id] && commentsMap[item.id].length > 0 ? (
                          commentsMap[item.id].map((comment) => {
                            const isAuthor = currentUser && (currentUser.sub === comment.author?.email || currentUser.username === comment.author?.username || currentUser.id === comment.user_id)

                            return (
                              <div key={comment.id} className="text-sm bg-white p-3 rounded-lg border border-gray-200 shadow-sm">
                                <div className="flex justify-between items-center mb-1">
                                  <span className="font-semibold text-gray-700">{comment.author?.username}</span>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs text-gray-400">{new Date(comment.created_at).toLocaleDateString()}</span>
                                    {isAuthor && (
                                      <button
                                        onClick={() => handleDeleteComment(comment.id, item.id)}
                                        className="text-xs text-orange-500 hover:text-orange-700 font-medium transition"
                                      >
                                        삭제
                                      </button>
                                    )}
                                  </div>
                                </div>
                                <p className="text-gray-600">{comment.content}</p>
                              </div>
                            )
                          })
                        ) : (
                          <div className="text-center py-4 text-xs text-gray-400">등록된 댓글이 없습니다. 첫 댓글을 남겨보세요!</div>
                        )}
                      </div>
                      
                      <CommentForm 
                        newsId={item.id} 
                        onCommentAdded={() => {
                          fetchCommentsForNews(item.id)
                        }} 
                      />
                    </div>
                  )}
                </div>
              )
            })}
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