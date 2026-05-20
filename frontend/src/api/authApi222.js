import api from './axios'

export const authApi = {
  // 회원가입
  signup: (userData) => 
    api.post('/auth/signup', userData),

  // 로그인 (OAuth2 형식: form-data)
  login: (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    return api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 내 정보 조회
  getMe: (token) => 
    api.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    }),

  // ✅ 내가 쓴 댓글 목록 조회
  getMyComments: (token) =>
    api.get('/auth/me/comments', {
      headers: { Authorization: `Bearer ${token}` }
    }),
}
