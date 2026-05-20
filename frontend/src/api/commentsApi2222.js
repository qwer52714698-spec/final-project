import api from './axios'

export const commentsApi = {
  // 댓글 목록 조회 (로그인 불필요)
  getComments: (newsId) => 
    api.get(`/news/${newsId}/comments`),

  // 댓글 작성 (로그인 필요 - Authorization 헤더 필요)
  createComment: (newsId, content, token) => 
    api.post(`/news/${newsId}/comments`, 
      { content }, 
      { headers: { Authorization: `Bearer ${token}` } }
    ),

  // 🆕 댓글 수정 (로그인 필요 - 본인만 수정 가능)
  updateComment: (commentId, content, token) =>
    api.put(`/comments/${commentId}`,
      { content },
      { headers: { Authorization: `Bearer ${token}` } }
    ),

  // 댓글 삭제 (로그인 필요 - 본인만 삭제 가능)
  deleteComment: (commentId, token) => {
    const cleanToken = token && token.startsWith('Bearer ') 
      ? token.replace('Bearer ', '') 
      : token

    return api.delete(`/comments/${commentId}`, 
      { headers: { Authorization: `Bearer ${cleanToken}` } }
    )
  },
}
