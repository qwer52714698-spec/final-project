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

  // 내 정보 조회 (미사용 - 필요시 구현)
  getMe: (token) => 
    api.get('/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    }),
}
