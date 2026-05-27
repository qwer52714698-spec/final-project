import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { commentsApi } from '../api/commentsApi'

function CommentForm({ newsId, onCommentAdded }) {
  const { isAuthenticated, user } = useAuth()
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!content.trim()) {
      alert('댓글 내용을 입력해주세요.')
      return
    }

    setLoading(true)
    try {
      const savedToken = localStorage.getItem('token')
      const tokenWithBearer = savedToken && !savedToken.startsWith('Bearer ')
        ? `Bearer ${savedToken}`
        : savedToken

      const response = await commentsApi.createComment(newsId, content, tokenWithBearer)
      setContent('')
      if (onCommentAdded) {
        onCommentAdded()
      }
      alert('댓글이 작성되었습니다.')
    } catch (error) {
      console.error('댓글 작성 실패:', error)
      const status = error.response?.status
      const detail = error.response?.data?.detail
      if (status === 401) {
        alert('로그인이 만료되었습니다. 다시 로그인해주세요.')
      } else {
        alert(detail || '댓글 작성에 실패했습니다.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-bold mb-4">댓글 작성</h3>

      {!isAuthenticated ? (
        <div className="text-center py-8 text-gray-500">
          댓글을 작성하려면 로그인이 필요합니다.
          <div className="mt-4">
            <a href="/login" className="text-blue-600 hover:underline">
              로그인하러 가기
            </a>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <div className="mb-3 text-sm text-gray-600">
            <span className="font-medium">{user?.username}</span>님으로 댓글 작성
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="댓글을 입력하세요..."
            className="w-full border border-gray-300 rounded-lg p-3 mb-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="3"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            >
              {loading ? '작성 중...' : '댓글 작성'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

export default CommentForm