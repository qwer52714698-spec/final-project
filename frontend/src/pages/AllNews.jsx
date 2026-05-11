import { useState, useEffect } from 'react'
import { newsApi } from '../api/newsApi'
import NewsCard from '../components/NewsCard'

function AllNews() {
  const [news, setNews] = useState([])
  const [sectors, setSectors] = useState([])
  const [selectedSector, setSelectedSector] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSectors()
  }, [])

  useEffect(() => {
    loadNews()
  }, [selectedSector])

  const loadSectors = async () => {
    try {
      const response = await newsApi.getSectors()
      setSectors(response.data)
    } catch (error) {
      console.error('섹터 로딩 실패:', error)
    }
  }

  const loadNews = async () => {
    try {
      const response = await newsApi.getAllNews(50, 0, selectedSector)
      setNews(response.data)
    } catch (error) {
      console.error('뉴스 로딩 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeAll = async () => {
    try {
      await newsApi.analyzeNews()
      alert('AI 감성 분석을 시작했습니다. 잠시 후 새로고침 해주세요.')
    } catch (error) {
      console.error('분석 실패:', error)
      alert('분석에 실패했습니다.')
    }
  }

  if (loading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">전체 뉴스</h1>
        <button
          onClick={handleAnalyzeAll}
          className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition"
        >
          AI 감성 분석
        </button>
      </div>

      <div className="mb-6 flex gap-2 flex-wrap">
        <button
          onClick={() => setSelectedSector(null)}
          className={`px-4 py-2 rounded-lg transition ${
            selectedSector === null 
              ? 'bg-blue-600 text-white' 
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          전체
        </button>
        {sectors.map(sector => (
          <button
            key={sector.id}
            onClick={() => setSelectedSector(sector.id)}
            className={`px-4 py-2 rounded-lg transition ${
              selectedSector === sector.id 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {sector.icon} {sector.name}
          </button>
        ))}
      </div>

      {news.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          뉴스가 없습니다.
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

export default AllNews
