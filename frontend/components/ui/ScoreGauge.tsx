interface ScoreGaugeProps {
  score: number
  type: "buy" | "sell"
  showStar?: boolean
  size?: "sm" | "md" | "lg"
}

function getColor(score: number, type: "buy" | "sell"): string {
  if (score <= 30) return "bg-stone-300"
  if (score <= 50) return "bg-yellow-400"
  if (score <= 70) return "bg-orange-400"
  if (type === "buy") return score <= 85 ? "bg-emerald-500" : "bg-emerald-700"
  return score <= 85 ? "bg-red-500" : "bg-red-700"
}

function getLabel(score: number): string {
  if (score <= 30) return "신호 없음"
  if (score <= 50) return "약한 신호"
  if (score <= 70) return "중간 신호"
  if (score <= 85) return "강한 신호"
  return "매우 강한 신호"
}

export default function ScoreGauge({ score, type, showStar = false, size = "md" }: ScoreGaugeProps) {
  const color = getColor(score, type)
  const label = getLabel(score)
  const pct = Math.min(100, score)

  const heightClass = size === "sm" ? "h-3" : size === "lg" ? "h-6" : "h-4"
  const textSize = size === "sm" ? "text-xs" : size === "lg" ? "text-2xl font-bold" : "text-sm"

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1">
        <span className={`${textSize} font-semibold text-gray-700`}>
          {score}점
          {showStar && <span className="ml-1 text-yellow-500">★</span>}
        </span>
        <span className="text-xs text-gray-400">{label}</span>
      </div>
      <div className={`w-full ${heightClass} bg-gray-200 rounded-full overflow-hidden`}>
        <div
          className={`${heightClass} ${color} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
