"use client"

import { useState } from "react"
import type { Market } from "@/types"

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5100"

interface BacktestSignal {
  date: string
  score: number
  label: string
  entry_price: number
  exit_price: number
  return_pct: number
  win: boolean
}

interface BacktestResult {
  ticker: string
  market: Market
  threshold: number
  hold_days: number
  total_signals: number
  win_rate: number
  avg_return_pct: number
  max_loss_pct: number
  max_gain_pct: number
  signals: BacktestSignal[]
  error?: string
}

function StatCard({
  label, value, color = "gray",
}: {
  label: string
  value: string
  color?: "emerald" | "red" | "yellow" | "gray"
}) {
  const palette = {
    emerald: "bg-emerald-50 border-emerald-200 text-emerald-800",
    red:     "bg-red-50 border-red-200 text-red-700",
    yellow:  "bg-yellow-50 border-yellow-200 text-yellow-800",
    gray:    "bg-white border-gray-200 text-gray-700",
  }
  return (
    <div className={`rounded-xl border p-4 ${palette[color]}`}>
      <p className="text-xs opacity-60 mb-1">{label}</p>
      <p className="text-2xl font-bold font-mono">{value}</p>
    </div>
  )
}

function Verdict({ result }: { result: BacktestResult }) {
  if (result.total_signals === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-600">
        {result.threshold}점 이상 신호가 과거 데이터에서 발생하지 않았습니다. 임계점을 낮춰보세요.
      </div>
    )
  }
  const pct = result.win_rate * 100
  const [cls, msg] =
    pct >= 60 ? ["bg-emerald-50 border-emerald-200 text-emerald-800",
                  `승률 ${pct.toFixed(0)}% — 신호 신뢰도 높음. 이 설정으로 실거래 활용 가능합니다.`]
    : pct >= 50 ? ["bg-yellow-50 border-yellow-200 text-yellow-800",
                   `승률 ${pct.toFixed(0)}% — 보통 수준. 임계점을 높이거나 보유 기간을 조정해보세요.`]
    :             ["bg-red-50 border-red-200 text-red-700",
                   `승률 ${pct.toFixed(0)}% — 신뢰도 낮음. 이 신호만으로 실거래는 위험합니다.`]

  return <div className={`rounded-xl border p-4 text-sm ${cls}`}>{msg}</div>
}

export default function BacktestPanel() {
  const [ticker,    setTicker]    = useState("")
  const [market,    setMarket]    = useState<Market>("KRX")
  const [threshold, setThreshold] = useState(25)
  const [holdDays,  setHoldDays]  = useState(5)
  const [loading,   setLoading]   = useState(false)
  const [result,    setResult]    = useState<BacktestResult | null>(null)
  const [error,     setError]     = useState<string | null>(null)

  const run = async () => {
    if (!ticker.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch(
        `${BASE_URL}/api/backtest?ticker=${ticker.trim().toUpperCase()}&market=${market}&threshold=${threshold}&hold_days=${holdDays}`
      )
      const data: BacktestResult = await res.json()
      if (data.error) throw new Error(data.error)
      setResult(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "오류 발생")
    } finally {
      setLoading(false)
    }
  }

  const fmtPrice = (p: number) =>
    market === "US" ? `$${p.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
                    : `${p.toLocaleString("ko-KR")}원`

  return (
    <div className="space-y-4">

      {/* 입력 패널 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-lg font-bold text-gray-800 mb-1">신호 백테스팅</h2>
        <p className="text-xs text-gray-400 mb-4">
          과거 데이터에서 신호 발생 시점을 찾아 이후 수익률을 계산합니다.
          기관/외국인·뉴스는 과거 데이터 미보유 → 중립값 처리. 실제 라이브 점수보다 낮게 나오므로 임계점 20~30점 권장.
        </p>

        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-xs text-gray-500 block mb-1">티커</label>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              placeholder="005930 / NVDA"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-36 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">시장</label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as Market)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="KRX">한국 (KRX)</option>
              <option value="US">미국 (US)</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">신호 임계점</label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                min={20} max={90} step={5}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-20 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-xs text-gray-400">점 이상</span>
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 block mb-1">보유 일수</label>
            <div className="flex items-center gap-1">
              <input
                type="number"
                value={holdDays}
                onChange={(e) => setHoldDays(Number(e.target.value))}
                min={1} max={20}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-16 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-xs text-gray-400">일 후 청산</span>
            </div>
          </div>

          <button
            onClick={run}
            disabled={loading || !ticker.trim()}
            className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {loading ? "분석 중..." : "실행"}
          </button>
        </div>
      </div>

      {/* 에러 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          오류: {error}
        </div>
      )}

      {/* 로딩 */}
      {loading && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-4xl mb-3 animate-pulse">📊</div>
          <p>과거 데이터 분석 중... (최대 20초 소요)</p>
        </div>
      )}

      {/* 결과 */}
      {result && !loading && (
        <>
          {/* 통계 카드 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="총 신호 횟수" value={`${result.total_signals}회`} />
            <StatCard
              label="승률"
              value={`${(result.win_rate * 100).toFixed(1)}%`}
              color={result.win_rate >= 0.6 ? "emerald" : result.win_rate >= 0.5 ? "yellow" : "red"}
            />
            <StatCard
              label="평균 수익률"
              value={`${result.avg_return_pct >= 0 ? "+" : ""}${result.avg_return_pct.toFixed(2)}%`}
              color={result.avg_return_pct > 0 ? "emerald" : "red"}
            />
            <StatCard label="최대 손실" value={`${result.max_loss_pct.toFixed(2)}%`} color="red" />
          </div>

          {/* 판정 */}
          <Verdict result={result} />

          {/* 신호 기록 테이블 */}
          {result.signals.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-700">
                  신호 발생 기록
                  <span className="ml-2 text-xs font-normal text-gray-400">
                    ({result.hold_days}일 후 수익률 기준)
                  </span>
                </h3>
                <span className="text-xs text-gray-400">
                  {result.signals.filter((s) => s.win).length}승 {result.signals.filter((s) => !s.win).length}패
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wide">
                      <th className="px-4 py-2 text-left">날짜</th>
                      <th className="px-4 py-2 text-right">점수</th>
                      <th className="px-4 py-2 text-right">진입가</th>
                      <th className="px-4 py-2 text-right">청산가</th>
                      <th className="px-4 py-2 text-right">{result.hold_days}일 수익률</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.signals.map((s) => (
                      <tr key={s.date} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="px-4 py-2.5 text-gray-600 font-mono text-xs">{s.date}</td>
                        <td className="px-4 py-2.5 text-right">
                          <span className="font-mono font-semibold text-gray-800">{s.score}</span>
                          <span className="ml-1 text-xs text-gray-400">({s.label})</span>
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-gray-600 text-xs">
                          {fmtPrice(s.entry_price)}
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-gray-600 text-xs">
                          {fmtPrice(s.exit_price)}
                        </td>
                        <td className={`px-4 py-2.5 text-right font-mono font-bold ${s.win ? "text-emerald-600" : "text-red-500"}`}>
                          {s.return_pct >= 0 ? "+" : ""}{s.return_pct.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
