import type { SignalScore } from "@/types"
import ScoreGauge from "@/components/ui/ScoreGauge"

const SIGNAL_NAMES: Record<string, string> = {
  s1_institutional_flow: "기관+외국인 순매도",
  s2_price_rise:         "저점 대비 상승",
  s3_news_sentiment:     "부정 뉴스",
  s4_rsi:                "RSI 과매수",
  s5_macd:               "MACD 데드크로스",
  s6_volume:             "거래량 급증+음봉",
  s7_bollinger:          "볼린저 상단",
  s8_stochastic:         "스토캐스틱 과매수",
  s9_short_ratio:        "공매도 급증",
  s10_ma_alignment:      "이평선 역배열",
}

const SIGNAL_DESC: Record<string, string> = {
  s1_institutional_flow: "기관·외국인이 동시에 3일 이상 순매도 시 강한 매도 신호",
  s2_price_rise:         "30일 저점 대비 30% 이상 상승 시 차익실현 구간",
  s3_news_sentiment:     "AI가 분석한 최근 뉴스 부정도 — 0.5 미만이면 부정",
  s4_rsi:                "RSI 65 초과: 과매수 구간, 55 초과: 약한 신호",
  s5_macd:               "MACD선이 시그널선을 위에서 아래로 교차 (데드크로스)",
  s6_volume:             "전일 대비 거래량 2배 이상 + 음봉 마감",
  s7_bollinger:          "주가가 볼린저밴드 상단을 터치하거나 이탈 후 복귀",
  s8_stochastic:         "스토캐스틱 K값 80 초과 과매수 구간 + 하향 크로스",
  s9_short_ratio:        "공매도 비율이 연속 증가 = 공매도 세력 유입",
  s10_ma_alignment:      "5일 < 20일 < 60일 이평선 역배열 = 하락 추세 확인",
}

export default function SellScoreCard({ score }: { score: SignalScore }) {
  return (
    <div className="bg-white rounded-xl border border-red-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold text-red-700">매도 신호</h3>
        {score.confluence_bonus > 0 && (
          <span className="text-xs bg-yellow-100 text-yellow-700 border border-yellow-300 px-2 py-0.5 rounded">
            ★ {score.confluence_count}개 카테고리 동시 충족 +{score.confluence_bonus}점
          </span>
        )}
      </div>

      <ScoreGauge score={score.total} type="sell" showStar={score.confluence_bonus > 0} size="lg" />

      <div className="mt-4 space-y-3">
        {Object.entries(score.breakdown).map(([key, item]) => {
          const pct = item.max > 0 ? (item.score / item.max) * 100 : 0
          const active = item.score > 0
          return (
            <div key={key} className="group relative">
              <div className="flex items-center gap-2">
                <span className={`text-xs w-28 shrink-0 ${active ? "text-red-700 font-semibold" : "text-gray-400"}`}>
                  {SIGNAL_NAMES[key] || key}
                </span>
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${active ? "bg-red-400" : "bg-gray-200"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className={`text-xs font-mono w-10 text-right shrink-0 ${active ? "text-red-600 font-bold" : "text-gray-300"}`}>
                  {item.score}/{item.max}
                </span>
              </div>

              {/* 현재값 주석 */}
              {item.detail && (
                <div className="flex gap-2 mt-0.5">
                  <span className="w-28 shrink-0" />
                  <span className={`text-xs ${active ? "text-red-500" : "text-gray-400"}`}>
                    {item.detail}
                  </span>
                </div>
              )}

              {/* 호버 설명 */}
              {SIGNAL_DESC[key] && (
                <div className="absolute left-0 top-full mt-1 z-10 hidden group-hover:block
                  bg-gray-800 text-white text-xs rounded-lg px-3 py-2 w-64 shadow-lg leading-relaxed">
                  {SIGNAL_DESC[key]}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
