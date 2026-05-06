function NewsCard({ news }) {
  const getSentimentColor = (label) => {
    switch (label) {
      case 'positive': return 'text-green-600 bg-green-50'
      case 'negative': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getSentimentText = (label) => {
    switch (label) {
      case 'positive': return '긍정'
      case 'negative': return '부정'
      default: return '중립'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('ko-KR', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 flex-1">
          {news.title}
        </h3>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ml-4 ${getSentimentColor(news.sentiment_label)}`}>
          {getSentimentText(news.sentiment_label)} {news.sentiment_score?.toFixed(2)}
        </span>
      </div>

      {news.ai_summary && (
        <p className="text-gray-700 mb-3 line-clamp-2">
          {news.ai_summary}
        </p>
      )}

      <div className="flex justify-between items-center text-sm text-gray-500">
        <span>{formatDate(news.published_at)}</span>
        {news.url && (
          <a 
            href={news.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            원문 보기 →
          </a>
        )}
      </div>
    </div>
  )
}

export default NewsCard
