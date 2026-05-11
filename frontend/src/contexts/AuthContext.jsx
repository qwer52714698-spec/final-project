import { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '../api/authApi'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  // 초기 로드: localStorage에서 토큰/유저 정보 복원
  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')

    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  // 로그인
  const login = async (username, password) => {
    try {
      const response = await authApi.login(username, password)
      const { access_token, user: userData } = response.data

      // 토큰과 유저 정보 저장
      setToken(access_token)
      setUser(userData)
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))

      return { success: true }
    } catch (error) {
      console.error('로그인 실패:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || '로그인에 실패했습니다.' 
      }
    }
  }

  // 회원가입
  const signup = async (userData) => {
    try {
      await authApi.signup(userData)
      return { success: true }
    } catch (error) {
      console.error('회원가입 실패:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || '회원가입에 실패했습니다.' 
      }
    }
  }

  // 로그아웃
  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const value = {
    user,
    token,
    isAuthenticated: !!token,
    login,
    signup,
    logout,
    loading,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
