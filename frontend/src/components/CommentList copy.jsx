import { useState, useEffect } from 'react'
import { commentsApi } from '../api/commentsApi'
import { useAuth } from '../contexts/AuthContext'

function CommentList({ newsId }) {
  const { user } = useAuth()  // 🆕 현재 로그인 유저 정보
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadComments()
  }, [newsId])

  const loadComments = async () => {
    try {
      const response = await commentsApi.getComments(newsId)
      setComments(response.data)
    } catch (error) {
      console.error('댓글 로딩 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (commentId) => {
    if (!confirm('댓글을 삭제하시겠습니까?')) return

    const token = localStorage.getItem('token')
    if (!token) {
      alert('로그인이 필요합니다.')
      return
    }

    try {
      await commentsApi.deleteComment(commentId, token)
      alert('댓글이 삭제되었습니다.')
      loadComments()
    } catch (error) {
      console.error('댓글 삭제 실패:', error)
      alert('댓글 삭제에 실패했습니다. 본인의 댓글만 삭제할 수 있습니다.')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return <div className="text-center py-4 text-gray-500">댓글 로딩 중...</div>
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-bold mb-4">
        💬 댓글 ({comments.length})
      </h3>

      {comments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          아직 댓글이 없습니다. 첫 댓글을 작성해보세요!
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map(comment => (
            <div 
              key={comment.id} 
              className="border-b border-gray-200 pb-4 last:border-0"
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">
                    {comment.author?.username || '익명'}
                  </span>
                  <span className="text-sm text-gray-500">
                    {formatDate(comment.created_at)}
                  </span>
                </div>

                {/* 🆕 본인 댓글일 때만 삭제 버튼 표시 */}
                {user && comment.author && user.id === comment.author.id && (
                  <button
                    onClick={() => handleDelete(comment.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    삭제
                  </button>
                )}
              </div>

              <p className="text-gray-700 whitespace-pre-wrap">
                {comment.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default CommentList
