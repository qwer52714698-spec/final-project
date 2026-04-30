import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <nav className="bg-white shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="text-xl font-bold text-blue-600">
            📈 주식 트렌드 예측
          </Link>
          <div className="flex gap-6">
            <Link to="/" className="text-gray-700 hover:text-blue-600 font-medium">
              대시보드
            </Link>
            <Link to="/news" className="text-gray-700 hover:text-blue-600 font-medium">
              전체 뉴스
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
