import api from './axios'

export const commentsApi = {
  getComments: (newsId) => 
    api.get(`/news/${newsId}/comments`),

  createComment: (newsId, content, token) => {
    const cleanToken = token && token.startsWith('Bearer ') 
      ? token.replace('Bearer ', '') 
      : token

    return api.post(`/news/${newsId}/comments`, 
      { content }, 
      { headers: { Authorization: `Bearer ${cleanToken}` } }
    )
  },

  deleteComment: (commentId, token) => {
    const cleanToken = token && token.startsWith('Bearer ') 
      ? token.replace('Bearer ', '') 
      : token

    return api.delete(`/comments/${commentId}`, 
      { headers: { Authorization: `Bearer ${cleanToken}` } }
    )
  },
}