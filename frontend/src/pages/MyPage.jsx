import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../api/authApi'

const SECTOR_COLORS = {
  '반도체': { bg: 'bg-blue-50', text: 'text-blue-700' },
  '2차전지': { bg: 'bg-green-50', text: 'text-green-700' },
  '자동차': { bg: 'bg-yellow-50', text: 'text-yellow-700' },
  'AI/IT': { bg: 'bg-purple-50', text: 'text-purple-700' },
  '바이오/제약': { bg: 'bg-pink-50', text: 'text-pink-700' },
  '금융': { bg: 'bg-indigo-50', text: 'text-indigo-700' },
  '에너지/화학': { bg: 'bg-orange-50', text: 'text-orange-700' },
  '산업재': { bg: 'bg-gray-100', text: 'text-gray-700' },
  '소비재': { bg: 'bg-red-50', text: 'text-red-700' },
}

function MyPage() {
  const { user, token, isAuthenticated, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [comments, setComments] = useState([])
  const [commentsLoading, setCommentsLoading] = useState(true)

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    loadMyComments()
  }, [authLoading, isAuthenticated])

  const loadMyComments = async () => {
    try {
      const response = await authApi.getMyComments(token)
      setComments(response.data)
    } catch (error) {
      console.error('댓글 로딩 실패:', error)
    } finally {
      setCommentsLoading(false)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getSectorColor = (sectorName) => {
    return SECTOR_COLORS[sectorName] || { bg: 'bg-gray-100', text: 'text-gray-700' }
  }

  const handleGoToNews = (newsId, sectorId) => {
    navigate(`/sector/${sectorId}/news?newsId=${newsId}`)
  }

  if (authLoading || commentsLoading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6 mb-8 flex items-center gap-4">
        <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xl font-bold">
          {user?.username?.charAt(0).toUpperCase()}
        </div>
        <div>
          <div className="text-lg font-bold text-gray-900">{user?.username}</div>
          <div className="text-sm text-gray-500">{user?.email}</div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">내가 쓴 댓글</h2>
        <span className="text-sm text-gray-500">총 {comments.length}개</span>
      </div>

      {comments.length === 0 ? (
        <div className="text-center py-20 text-gray-500 bg-white rounded-lg shadow-md">
          아직 작성한 댓글이 없습니다.
        </div>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => {
            const sectorName = comment.news?.sector?.name
            const sectorColor = getSectorColor(sectorName)

            return (
              <div key={comment.id} className="bg-white rounded-lg shadow-md p-5">
                <div className="flex items-start gap-2 mb-3">
                  <span className="text-blue-600 text-sm mt-0.5">📰</span>
                  <div className="flex-1">
                    <span className="text-sm font-medium text-blue-700 leading-snug">
                      {comment.news?.title || '뉴스 정보 없음'}
                    </span>
                  </div>
                  {sectorName && (
                    <span
                      className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full ${sectorColor.bg} ${sectorColor.text}`}
                    >
                      {sectorName}
                    </span>
                  )}
                </div>

                <p className="text-gray-800 text-sm mb-3 whitespace-pre-wrap">{comment.content}</p>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">{formatDate(comment.created_at)}</span>
                  {comment.news_id && comment.news?.sector_id && (
                    <button
                      onClick={() => handleGoToNews(comment.news_id, comment.news.sector_id)}
                      className="flex items-center gap-1 text-xs text-blue-600 border border-blue-200 bg-blue-50 rounded-lg px-3 py-1.5 hover:bg-blue-100 transition"
                    >
                      뉴스 보러가기 →
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default MyPage
