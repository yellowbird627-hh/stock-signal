"use client"

import { useEffect, useState } from "react"
import { useSignalStore } from "@/store/useSignalStore"
import PortfolioDashboard from "@/components/panels/PortfolioDashboard"
import StockSearch from "@/components/panels/StockSearch"
import BuyScoreCard from "@/components/panels/BuyScoreCard"
import SellScoreCard from "@/components/panels/SellScoreCard"
import NewsSentimentPanel from "@/components/panels/NewsSentimentPanel"
import AIRecommendation from "@/components/panels/AIRecommendation"
import IndicatorGuide from "@/components/panels/IndicatorGuide"
import TradingSuitability from "@/components/ui/TradingSuitability"

// ── 비밀번호 게이트 ────────────────────────────────────────────────────────────

function PasswordGate() {
  const { authenticate } = useSignalStore()
  const [input, setInput] = useState("")
  const [error, setError] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const ok = authenticate(input)
    if (!ok) setError(true)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white rounded-2xl border border-gray-200 p-8 w-full max-w-sm shadow-sm">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">📈</div>
          <h1 className="text-xl font-bold text-gray-800">주식 매매 신호</h1>
          <p className="text-sm text-gray-400 mt-1">비밀번호를 입력하세요</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="password"
            value={input}
            onChange={(e) => { setInput(e.target.value); setError(false) }}
            placeholder="비밀번호"
            className={`w-full border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              error ? "border-red-400" : "border-gray-300"
            }`}
            autoFocus
          />
          {error && <p className="text-xs text-red-500">비밀번호가 틀렸습니다.</p>}
          <button
            type="submit"
            className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 transition"
          >
            입장
          </button>
        </form>
      </div>
    </div>
  )
}

// ── 개별 종목 뷰 ──────────────────────────────────────────────────────────────

function DetailView() {
  const { result, loading, error } = useSignalStore()

  if (loading) {
    return (
      <div className="text-center py-20 text-gray-400">
        <div className="text-4xl mb-3 animate-pulse">🔍</div>
        <p>종목 분석 중...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
        오류: {error}
      </div>
    )
  }

  if (!result) {
    return (
      <div className="text-center py-20 text-gray-400">
        <div className="text-4xl mb-3">📊</div>
        <p>위에서 종목을 선택하거나 티커를 입력하세요.</p>
      </div>
    )
  }

  const changeColor = result.change_pct >= 0 ? "text-red-600" : "text-blue-600"
  const changeSign = result.change_pct >= 0 ? "+" : ""
  const priceFormatted =
    result.market === "US"
      ? `$${result.price.toLocaleString("en-US", { minimumFractionDigits: 2 })}`
      : `${result.price.toLocaleString("ko-KR")}원`

  return (
    <div className="space-y-4">
      {/* 종목 헤더 */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              {result.company_name}
              <span className="ml-2 text-sm font-normal text-gray-400">
                {result.ticker} · {result.market}
              </span>
            </h2>
            <div className="flex items-center gap-3 mt-1 flex-wrap">
              <span className="text-2xl font-mono font-semibold text-gray-800">{priceFormatted}</span>
              <span className={`text-base font-mono ${changeColor}`}>
                {changeSign}{result.change_pct.toFixed(2)}%
              </span>
              <TradingSuitability suitability={result.trading_suitability} atrPct={result.atr_pct} />
            </div>
          </div>
          <p className="text-xs text-gray-400">
            {new Date(result.data_timestamp).toLocaleString("ko-KR")} 기준 (전일 종가)
          </p>
        </div>

        {result.trading_suitability === "low" && (
          <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
            변동성이 낮아 단타 수익 기회가 제한적일 수 있습니다 (ATR {result.atr_pct}%)
          </div>
        )}

        {result.data_limitations.length > 0 && (
          <div className="mt-2 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-600 space-y-0.5">
            {result.data_limitations.map((l, i) => <div key={i}>ℹ️ {l}</div>)}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BuyScoreCard score={result.buy} />
        <SellScoreCard score={result.sell} />
      </div>

      <NewsSentimentPanel news={result.news} sentiment={result.news_sentiment} />
    </div>
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Page() {
  const { isAuthenticated, activeTab, setActiveTab } = useSignalStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true) }, [])

  if (!mounted) return null
  if (!isAuthenticated) return <PasswordGate />

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-base font-bold text-gray-800">📈 주식 매매 신호 대시보드</h1>
          <p className="text-xs text-gray-400">{new Date().toLocaleDateString("ko-KR")}</p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-5">
        <div className="flex gap-1 bg-white rounded-xl border border-gray-200 p-1 flex-wrap">
          {([
            { key: "portfolio",       label: "전체 포트폴리오" },
            { key: "recommendation",  label: "🤖 AI 추천" },
            { key: "detail",          label: "개별 종목 분석" },
            { key: "guide",           label: "지표 가이드" },
          ] as const).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                activeTab === key
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-gray-500 hover:text-gray-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {activeTab === "portfolio" && <PortfolioDashboard />}
        {activeTab === "recommendation" && <AIRecommendation />}
        {activeTab === "guide" && <IndicatorGuide />}
        {activeTab === "detail" && (
          <>
            <StockSearch />
            <DetailView />
          </>
        )}
      </main>
    </div>
  )
}
