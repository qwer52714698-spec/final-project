import { useState, useEffect } from 'react'
import { newsApi } from '../api/newsApi'
import NewsCard from '../components/NewsCard'
import CommentList from '../components/CommentList'
import CommentForm from '../components/CommentForm'

function AllNews() {
  const [news, setNews] = useState([])
  const [sectors, setSectors] = useState([])
  const [selectedSector, setSelectedSector] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedNews, setSelectedNews] = useState(null) // 선택된 뉴스 (댓글 보기용)

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

  const handleNewsClick = (newsItem) => {
    setSelectedNews(newsItem)
  }

  const handleBackToList = () => {
    setSelectedNews(null)
  }

  if (loading) {
    return <div className="text-center py-20">로딩 중...</div>
  }

  // 뉴스 상세보기 + 댓글
  if (selectedNews) {
    return (
      <div>
        <button
          onClick={handleBackToList}
          className="mb-6 text-blue-600 hover:text-blue-800 font-medium"
        >
          ← 목록으로 돌아가기
        </button>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-2xl font-bold mb-4">{selectedNews.title}</h1>

          {selectedNews.ai_summary && (
            <div className="bg-blue-50 p-4 rounded-lg mb-4">
              <h3 className="font-semibold mb-2">📝 AI 요약</h3>
              <p className="text-gray-700">{selectedNews.ai_summary}</p>
            </div>
          )}

          {selectedNews.content && (
            <div className="mb-4">
              <p className="text-gray-700 whitespace-pre-wrap">{selectedNews.content}</p>
            </div>
          )}

          <div className="flex justify-between items-center text-sm text-gray-500 border-t pt-4">
            <span>{new Date(selectedNews.published_at).toLocaleDateString('ko-KR')}</span>
            {selectedNews.url && (
              <a 
                href={selectedNews.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                원문 보기 →
              </a>
            )}
          </div>
        </div>

        {/* 🆕 댓글 작성 폼 */}
        <CommentForm 
          newsId={selectedNews.id} 
          onCommentAdded={() => {
            setSelectedNews({...selectedNews})
          }}
        />

        {/* 🆕 댓글 목록 */}
        <CommentList key={selectedNews.id} newsId={selectedNews.id} />
      </div>
    )
  }

  // 뉴스 목록
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
            <div key={item.id} onClick={() => handleNewsClick(item)} className="cursor-pointer">
              <NewsCard news={item} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default AllNews
