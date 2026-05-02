"use client"

import { useEffect, useState } from "react"
import { useSignalStore } from "@/store/useSignalStore"
import type { Market, PortfolioItem, SignalLabel } from "@/types"
import ScoreGauge from "@/components/ui/ScoreGauge"
import TradingSuitability from "@/components/ui/TradingSuitability"

type SortKey = "signal" | "buy" | "sell" | "change_pct"

const LABEL_RANK: Record<SignalLabel, number> = {
  very_strong: 4,
  strong: 3,
  moderate: 2,
  weak: 1,
  none: 0,
}

function signalRank(item: PortfolioItem): number {
  return Math.max(
    LABEL_RANK[item.buy_label ?? "none"],
    LABEL_RANK[item.sell_label ?? "none"],
  )
}

function formatPrice(price: number, market: string): string {
  if (market === "US") return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
  return `${price.toLocaleString("ko-KR")}원`
}

// ── 시그널 뱃지 ───────────────────────────────────────────────────────────────

function SignalBadge({ item }: { item: PortfolioItem }) {
  const buyRank = LABEL_RANK[item.buy_label ?? "none"]
  const sellRank = LABEL_RANK[item.sell_label ?? "none"]

  if (buyRank === 0 && sellRank === 0) {
    return <span className="text-xs text-gray-300 font-medium">중립</span>
  }

  const dominant = buyRank >= sellRank ? { label: item.buy_label, score: item.buy, side: "buy" } : { label: item.sell_label, score: item.sell, side: "sell" }

  const isStrong = dominant.label === "strong" || dominant.label === "very_strong"

  if (dominant.side === "buy") {
    return (
      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
        isStrong
          ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
          : "bg-emerald-50 text-emerald-500"
      }`}>
        {isStrong ? "▲ 강한 매수" : "▲ 매수"}
      </span>
    )
  }
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
      isStrong
        ? "bg-red-100 text-red-700 border border-red-300"
        : "bg-red-50 text-red-400"
    }`}>
      {isStrong ? "▼ 강한 매도" : "▼ 매도"}
    </span>
  )
}

// ── 종목 추가 패널 ─────────────────────────────────────────────────────────────

function AddStockPanel({ onAdded }: { onAdded: () => void }) {
  const { addStock } = useSignalStore()
  const [ticker, setTicker] = useState("")
  const [market, setMarket] = useState<Market>("KRX")
  const [loading, setLoading] = useState(false)
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null)

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ticker.trim()) return
    setLoading(true)
    setMsg(null)
    try {
      const name = await addStock(ticker.trim().toUpperCase(), market)
      setMsg({ type: "ok", text: `${name} 추가 완료` })
      setTicker("")
      onAdded()
    } catch (e: unknown) {
      const text = e instanceof Error ? e.message : "오류 발생"
      setMsg({ type: "err", text })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleAdd} className="flex items-center gap-2 flex-wrap">
      <input
        type="text"
        value={ticker}
        onChange={(e) => { setTicker(e.target.value.toUpperCase()); setMsg(null) }}
        placeholder="티커 입력 (예: 000660, NVDA)"
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm w-52 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <select
        value={market}
        onChange={(e) => setMarket(e.target.value as Market)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="KRX">한국 (KRX)</option>
        <option value="US">미국 (US)</option>
      </select>
      <button
        type="submit"
        disabled={loading || !ticker.trim()}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
      >
        {loading ? "추가 중..." : "+ 종목 추가"}
      </button>
      {msg && (
        <span className={`text-xs ${msg.type === "ok" ? "text-emerald-600" : "text-red-500"}`}>
          {msg.text}
        </span>
      )}
    </form>
  )
}

// ── 종목 행 ───────────────────────────────────────────────────────────────────

function StockRow({
  item,
  onSelect,
  onRemove,
}: {
  item: PortfolioItem
  onSelect: (t: string, m: Market) => void
  onRemove: (t: string, m: Market) => void
}) {
  const [removing, setRemoving] = useState(false)
  const changeColor = item.change_pct >= 0 ? "text-red-600" : "text-blue-600"
  const changeSign = item.change_pct >= 0 ? "+" : ""

  const handleRemove = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm(`${item.name}을(를) 삭제할까요?`)) return
    setRemoving(true)
    try {
      await onRemove(item.ticker, item.market)
    } finally {
      setRemoving(false)
    }
  }

  return (
    <tr
      className="border-b border-gray-100 hover:bg-blue-50 cursor-pointer transition group"
      onClick={() => onSelect(item.ticker, item.market)}
    >
      <td className="py-3 pr-4">
        <div className="flex items-center gap-2">
          <div>
            <div className="font-semibold text-gray-800">
              {item.name}
              {item.confluence_bonus > 0 && <span className="ml-1 text-yellow-500 text-xs">★</span>}
            </div>
            <div className="text-xs text-gray-400">{item.ticker} · {item.market}</div>
          </div>
        </div>
        {item.error && <div className="text-xs text-red-400 mt-0.5">분석 실패</div>}
      </td>
      <td className="py-3 pr-4">
        <SignalBadge item={item} />
      </td>
      <td className="py-3 pr-4">
        <ScoreGauge score={item.buy} type="buy" size="sm" />
      </td>
      <td className="py-3 pr-4">
        <ScoreGauge score={item.sell} type="sell" size="sm" />
      </td>
      <td className="py-3 pr-4 text-right font-mono text-gray-700">
        {formatPrice(item.price, item.market)}
      </td>
      <td className={`py-3 pr-4 text-right font-mono ${changeColor}`}>
        {changeSign}{item.change_pct.toFixed(2)}%
      </td>
      <td className="py-3 pr-4">
        <TradingSuitability suitability={item.suitability} atrPct={item.atr_pct} />
      </td>
      <td className="py-3 text-right">
        <button
          onClick={handleRemove}
          disabled={removing}
          className="opacity-0 group-hover:opacity-100 text-xs text-gray-400 hover:text-red-500 transition px-2 py-1 rounded"
          title="종목 삭제"
        >
          {removing ? "..." : "삭제"}
        </button>
      </td>
    </tr>
  )
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────────────

const REFRESH_INTERVAL_MS = 5 * 60 * 1000 // 5분

export default function PortfolioDashboard() {
  const {
    portfolio, portfolioLoading, portfolioError, portfolioTimestamp,
    fetchPortfolio, selectFromPortfolio, removeStock,
  } = useSignalStore()
  const [sortKey, setSortKey] = useState<SortKey>("signal")
  const [showAdd, setShowAdd] = useState(false)
  const [minutesAgo, setMinutesAgo] = useState(0)

  // 최초 로드 + 5분 자동 갱신
  useEffect(() => {
    fetchPortfolio()
    const interval = setInterval(fetchPortfolio, REFRESH_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  // "X분 전 갱신" 카운터 (1분마다 업데이트)
  useEffect(() => {
    if (!portfolioTimestamp) return
    const update = () => {
      setMinutesAgo(Math.floor((Date.now() - new Date(portfolioTimestamp).getTime()) / 60000))
    }
    update()
    const t = setInterval(update, 60000)
    return () => clearInterval(t)
  }, [portfolioTimestamp])

  const sorted = [...portfolio].sort((a, b) => {
    if (sortKey === "buy")       return b.buy - a.buy
    if (sortKey === "sell")      return b.sell - a.sell
    if (sortKey === "change_pct") return b.change_pct - a.change_pct
    // 신호강도: 강도 등급 우선, 동일 등급이면 실제 점수로 구분
    const rankDiff = signalRank(b) - signalRank(a)
    if (rankDiff !== 0) return rankDiff
    return Math.max(b.buy, b.sell) - Math.max(a.buy, a.sell)
  })

  const SortBtn = ({ k, label }: { k: SortKey; label: string }) => (
    <button
      onClick={() => setSortKey(k)}
      className={`text-xs px-2 py-1 rounded transition ${
        sortKey === k ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
      }`}
    >
      {label}
    </button>
  )

  const strongCount = sorted.filter(
    (s) => (s.buy_label === "strong" || s.buy_label === "very_strong") ||
           (s.sell_label === "strong" || s.sell_label === "very_strong")
  ).length

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-lg font-bold text-gray-800">
            전체 포트폴리오
            {strongCount > 0 && (
              <span className="ml-2 text-sm font-normal text-amber-600">
                강한 신호 {strongCount}개
              </span>
            )}
          </h2>
          {portfolioTimestamp && (
            <p className="text-xs text-gray-400 flex items-center gap-1.5">
              {minutesAgo === 0 ? "방금 갱신됨" : `${minutesAgo}분 전 갱신`}
              {portfolioLoading && portfolio.length > 0 && (
                <span className="inline-block w-3 h-3 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
              )}
              <span className="text-gray-300">· 5분마다 자동 갱신</span>
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-gray-500">정렬:</span>
          <SortBtn k="signal" label="신호강도" />
          <SortBtn k="buy"    label="매수점수" />
          <SortBtn k="sell"   label="매도점수" />
          <SortBtn k="change_pct" label="등락률" />
          <button
            onClick={() => setShowAdd((v) => !v)}
            className={`text-xs px-3 py-1 rounded border transition ${
              showAdd
                ? "bg-blue-50 border-blue-400 text-blue-700"
                : "border-gray-300 text-gray-600 hover:bg-gray-50"
            }`}
          >
            종목 관리
          </button>
          <button
            onClick={fetchPortfolio}
            disabled={portfolioLoading}
            className="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {portfolioLoading ? "분석 중..." : "새로고침"}
          </button>
        </div>
      </div>

      {/* 종목 추가 패널 */}
      {showAdd && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-xs text-blue-600 mb-3 font-medium">
            종목 추가 — 티커를 입력하면 이름을 자동으로 찾아옵니다.
            추가 후 <strong>새로고침</strong>을 눌러 점수를 확인하세요.
          </p>
          <AddStockPanel onAdded={() => {}} />
        </div>
      )}

      {portfolioError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
          오류: {portfolioError}
        </div>
      )}

      {portfolioLoading && portfolio.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-4xl mb-3">📊</div>
          <p>전체 종목 분석 중...</p>
          <p className="text-xs mt-1">종목 수에 따라 1~2분 소요될 수 있습니다</p>
        </div>
      )}

      {sorted.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-200 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="pb-2 pr-4">종목</th>
                <th className="pb-2 pr-4">신호</th>
                <th className="pb-2 pr-4 w-32">매수</th>
                <th className="pb-2 pr-4 w-32">매도</th>
                <th className="pb-2 pr-4 text-right">현재가</th>
                <th className="pb-2 pr-4 text-right">등락</th>
                <th className="pb-2 pr-4">단타 적합도</th>
                <th className="pb-2 w-12"></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((item) => (
                <StockRow
                  key={`${item.market}:${item.ticker}`}
                  item={item}
                  onSelect={selectFromPortfolio}
                  onRemove={removeStock}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!portfolioLoading && sorted.length === 0 && !portfolioError && (
        <div className="text-center py-16 text-gray-400">
          <p className="mb-3">종목이 없습니다.</p>
          <button
            onClick={() => setShowAdd(true)}
            className="text-sm text-blue-600 hover:underline"
          >
            종목 관리를 눌러 추가해보세요 →
          </button>
        </div>
      )}
    </div>
  )
}
