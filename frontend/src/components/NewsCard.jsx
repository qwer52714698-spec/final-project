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

  const explanation = news.sentiment_explanation

  const renderWeight = (weight) => {
    const prefix = weight > 0 ? '+' : ''
    return `${prefix}${weight.toFixed(2)}`
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-semibold text-gray-900 flex-1">
          {news.title}
        </h3>
        <div className="ml-4 flex items-center gap-2 shrink-0">
          <div className="relative group" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="w-5 h-5 rounded-full border border-gray-300 text-[11px] font-bold text-gray-500 bg-white hover:bg-gray-50"
            >
              ?
            </button>
            <div className="absolute right-0 top-7 z-20 hidden w-80 rounded-lg border border-gray-200 bg-white p-3 text-left text-xs text-gray-700 shadow-xl group-hover:block">
              <div className="font-semibold text-gray-900 mb-2">감성점수 기준</div>
              <div className="space-y-1 mb-3">
                <div>호재: {`score > ${explanation?.thresholds?.positive_over ?? 0.15}`}</div>
                <div>악재: {`score < ${explanation?.thresholds?.negative_under ?? -0.15}`}</div>
                <div>중립: {`${explanation?.thresholds?.neutral_range?.[0] ?? -0.15} ~ ${explanation?.thresholds?.neutral_range?.[1] ?? 0.15}`}</div>
              </div>

              <div className="font-semibold text-gray-900 mb-2">점수 근거</div>
              <div className="text-gray-600 mb-2">
                {explanation?.basis_note ?? '기사 내용과 투자 신호 키워드를 함께 반영합니다.'}
              </div>

              {explanation?.matched_terms?.length > 0 ? (
                <div className="space-y-1 mb-3">
                  {explanation.matched_terms.map((term, index) => (
                    <div key={`${term.term}-${index}`} className="flex items-center justify-between gap-3">
                      <span className={term.direction === 'positive' ? 'text-green-700' : 'text-red-700'}>
                        {term.term}
                      </span>
                      <span className="font-medium text-gray-700">{renderWeight(term.weight)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-gray-500 mb-3">뚜렷한 키워드 근거는 없고 문맥 중심으로 판단했습니다.</div>
              )}

              {explanation?.adjustments?.length > 0 && (
                <>
                  <div className="font-semibold text-gray-900 mb-2">보정 규칙</div>
                  <div className="space-y-1">
                    {explanation.adjustments.map((rule, index) => (
                      <div key={`${rule.rule}-${index}`} className="flex items-center justify-between gap-3 text-gray-600">
                        <span>{rule.rule}</span>
                        <span>{rule.effect}</span>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>

          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSentimentColor(news.sentiment_label)}`}>
            {getSentimentText(news.sentiment_label)} {news.sentiment_score?.toFixed(2)}
          </span>
        </div>
      </div>

      {news.ai_summary && (
        <p className="text-gray-700 mb-3 line-clamp-2">
          {news.ai_summary}
        </p>
      )}

      <div className="flex justify-between items-center text-sm text-gray-500">
        <div className="flex items-center gap-4">
          <span>{formatDate(news.published_at)}</span>
          <span className="text-gray-400">댓글 {news.comment_count ?? 0}</span>
        </div>
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