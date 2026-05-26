import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'
import UserMenu from './UserMenu'

function Navbar() {
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [sectors, setSectors] = useState([])

  useEffect(() => {
    const fetchSectors = async () => {
      try {
        const response = await newsApi.getSectors()
        setSectors(response.data || [])
      } catch (error) {
        console.error('네비게이션 섹터 로딩 실패:', error)
      }
    }
    fetchSectors()
  }, [])

  return (
    <nav 
      className="bg-white border-b border-gray-100 relative z-50"
      onMouseLeave={() => setIsOpen(false)}
    >
      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center">
            <img src="/logo_main.png" alt="Logo" className="h-12 w-auto object-contain" />
          </Link>
          
          <div className="flex items-center gap-8">
            <Link to="/" className="text-gray-600 hover:text-blue-600 font-medium transition text-sm">
              대시보드
            </Link>
            
            <button 
              onMouseEnter={() => setIsOpen(true)}
              className={`text-gray-600 hover:text-blue-600 font-medium h-16 flex items-center gap-1 transition text-sm relative after:absolute after:bottom-0 after:left-0 after:w-full after:h-0.5 after:bg-blue-600 after:transition-transform after:duration-200 ${isOpen ? 'text-blue-600 after:scale-x-100' : 'after:scale-x-0'}`}
            >
              섹터별 주식현황
            </button>

            <Link to="/news" className="text-gray-600 hover:text-blue-600 font-medium transition text-sm">
              전체 뉴스
            </Link>
            <UserMenu />
          </div>
        </div>
      </div>

      <div 
        className={`absolute left-0 w-full bg-white border-b border-gray-200/80 shadow-[0_20px_25px_-5px_rgba(0,0,0,0.05)] transition-all duration-300 origin-top overflow-hidden z-40 ${isOpen && sectors.length > 0 ? 'opacity-100 scale-y-100 h-auto py-10' : 'opacity-0 scale-y-0 h-0 py-0'}`}
        onMouseEnter={() => setIsOpen(true)}
      >
        <div className="container mx-auto px-8 max-w-7xl">
          <div className="grid grid-cols-4 gap-x-8 gap-y-6">
            {sectors.map((sector) => (
              <div
                key={sector.id}
                onClick={() => {
                  navigate(`/sector/${sector.id}/stocks`)
                  setIsOpen(false)
                }}
                className="group flex items-start gap-3.5 p-3 rounded-xl hover:bg-gray-50/80 cursor-pointer transition"
              >
                <div className="w-10 h-10 rounded-lg bg-gray-50 group-hover:bg-blue-50 flex items-center justify-center text-xl transition shrink-0 border border-gray-100">
                  {sector.icon || '💼'}
                </div>
                <div className="space-y-0.5 min-w-0">
                  <span className="font-semibold text-sm text-gray-900 group-hover:text-blue-600 transition block">
                    {sector.name} 현황
                  </span>
                  {sector.description && (
                    <span className="text-xs text-gray-400 block truncate">
                      {sector.description}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar