import type { NewsItem, NewsSentiment } from "@/types"

function SentimentBadge({ score }: { score: number }) {
  const label = score >= 0.7 ? "긍정" : score >= 0.4 ? "중립" : "부정"
  const color =
    score >= 0.7
      ? "bg-emerald-100 text-emerald-700"
      : score >= 0.4
      ? "bg-gray-100 text-gray-600"
      : "bg-red-100 text-red-700"
  return <span className={`text-xs px-1.5 py-0.5 rounded ${color}`}>{label}</span>
}

export default function NewsSentimentPanel({
  news,
  sentiment,
}: {
  news: NewsItem[]
  sentiment: NewsSentiment
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-bold text-gray-700">뉴스 감성 분석</h3>
        <div className="flex items-center gap-2">
          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all ${
                sentiment.score >= 0.7 ? "bg-emerald-500" : sentiment.score >= 0.4 ? "bg-gray-400" : "bg-red-500"
              }`}
              style={{ width: `${sentiment.score * 100}%` }}
            />
          </div>
          <span className="text-sm font-mono text-gray-600">
            {(sentiment.score * 100).toFixed(0)}점
          </span>
        </div>
      </div>

      {sentiment.reasoning && (
        <p className="text-sm text-gray-600 mb-3 italic">"{sentiment.reasoning}"</p>
      )}

      {sentiment.key_points.length > 0 && (
        <ul className="mb-3 space-y-1">
          {sentiment.key_points.map((p, i) => (
            <li key={i} className="text-xs text-gray-500 flex gap-1">
              <span className="text-gray-300">•</span>
              <span>{p}</span>
            </li>
          ))}
        </ul>
      )}

      {news.length === 0 ? (
        <p className="text-sm text-gray-400">최근 7일 내 뉴스가 없습니다.</p>
      ) : (
        <div className="space-y-2">
          {news.map((n, i) => (
            <div key={i} className="flex items-start justify-between gap-2">
              <a
                href={n.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-700 hover:text-blue-600 hover:underline flex-1"
              >
                {n.headline}
              </a>
              <div className="flex items-center gap-1 shrink-0">
                <SentimentBadge score={n.sentiment_score} />
                <span className="text-xs text-gray-400">{n.published_at}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
