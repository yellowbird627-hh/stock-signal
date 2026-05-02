"use client"

import { useEffect, useState } from "react"
import { useSignalStore } from "@/store/useSignalStore"
import type { Market, StockConfig } from "@/types"

export default function StockSearch() {
  const { fetchSignal, fetchStockList, stockList, loading, selectedTicker, selectedMarket } = useSignalStore()
  const [ticker, setTicker] = useState("")
  const [market, setMarket] = useState<Market>("KRX")

  useEffect(() => {
    fetchStockList()
  }, [])

  useEffect(() => {
    if (selectedTicker) setTicker(selectedTicker)
    if (selectedMarket) setMarket(selectedMarket)
  }, [selectedTicker, selectedMarket])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (ticker.trim()) fetchSignal(ticker.trim().toUpperCase(), market)
  }

  const handleSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value
    if (!val) return
    const [t, m] = val.split("|")
    setTicker(t)
    setMarket(m as Market)
    fetchSignal(t, m as Market)
  }

  const enabledStocks = stockList.filter((s: StockConfig) => s.enabled)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-600 mb-3">종목 선택</h3>
      <form onSubmit={handleSubmit} className="flex gap-2 flex-wrap">
        {/* 종목 목록 드롭다운 */}
        {enabledStocks.length > 0 && (
          <select
            onChange={handleSelect}
            value={selectedTicker ? `${selectedTicker}|${selectedMarket}` : ""}
            className="flex-1 min-w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">종목 선택...</option>
            {enabledStocks.map((s: StockConfig) => (
              <option key={`${s.ticker}|${s.market}`} value={`${s.ticker}|${s.market}`}>
                {s.name} ({s.ticker})
              </option>
            ))}
          </select>
        )}

        {/* 직접 입력 */}
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="티커 직접 입력 (예: 005930)"
          className="flex-1 min-w-40 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          {loading ? "분석 중..." : "분석"}
        </button>
      </form>
    </div>
  )
}
