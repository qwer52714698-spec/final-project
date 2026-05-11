import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { newsApi } from '../api/newsApi'
import NewsCard from '../components/NewsCard'

function SectorNews() {
  const { sectorId } = useParams()
  const navigate = useNavigate()
  const [news, setNews] = useState([])
  const [sector, setSector] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadNews()
    loadSectorInfo()
  }, [sectorId])

  const loadNews = async () => {
    try {
      const response = await newsApi.getNewsBySector(sectorId, 50)
      setNews(response.data)
    } catch (error) {
      console.error('뉴스 로딩 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadSectorInfo = async () => {
    try {
      const response = await newsApi.getSectors()
      const foundSector = response.data.find(s => s.id === parseInt(sectorId))
      setSector(foundSector)
    } catch (error) {
      console.error('섹터 정보 로딩 실패:', error)
    }
  }

  const handleCollectNews = async () => {
    try {
      await newsApi.collectNews(sectorId)
      alert('뉴스 수집을 시작했습니다. 잠시 후 새로고침 해주세요.')
    } catch (error) {
      console.error('뉴스 수집 실패:', error)
      alert('뉴스 수집에 실패했습니다.')
    }
  }

  if (loading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← 돌아가기
          </button>
          <h1 className="text-3xl font-bold">
            {sector?.icon} {sector?.name} 뉴스
          </h1>
        </div>
        <button
          onClick={handleCollectNews}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          뉴스 수집
        </button>
      </div>

      {news.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          아직 뉴스가 없습니다. 뉴스 수집 버튼을 눌러주세요.
        </div>
      ) : (
        <div className="space-y-4">
          {news.map(item => (
            <NewsCard key={item.id} news={item} />
          ))}
        </div>
      )}
    </div>
  )
}

export default SectorNews
