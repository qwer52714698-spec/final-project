import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

function UserMenu() {
  const { user, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    if (confirm('로그아웃 하시겠습니까?')) {
      logout()
      navigate('/')
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="flex gap-3">
        <button
          onClick={() => navigate('/login')}
          className="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium"
        >
          로그인
        </button>
        <button
          onClick={() => navigate('/signup')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          회원가입
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-4">
      <span className="text-gray-700">
        👤 <span className="font-medium">{user?.username}</span>님
      </span>
      <button
        onClick={handleLogout}
        className="px-4 py-2 text-gray-700 hover:text-red-600 font-medium"
      >
        로그아웃
      </button>
    </div>
  )
}

export default UserMenu
