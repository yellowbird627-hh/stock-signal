"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"
import { api } from "@/lib/api"
import type { Market, PortfolioItem, SignalResult, StockConfig } from "@/types"

type Tab = "portfolio" | "recommendation" | "detail" | "guide"

interface SignalStore {
  // 인증
  isAuthenticated: boolean
  authenticate: (password: string) => boolean

  // 탭
  activeTab: Tab
  setActiveTab: (tab: Tab) => void

  // 포트폴리오
  portfolio: PortfolioItem[]
  portfolioLoading: boolean
  portfolioError: string | null
  portfolioTimestamp: string | null
  fetchPortfolio: () => Promise<void>

  // 개별 종목
  selectedTicker: string | null
  selectedMarket: Market | null
  result: SignalResult | null
  loading: boolean
  error: string | null
  fetchSignal: (ticker: string, market: Market) => Promise<void>
  selectFromPortfolio: (ticker: string, market: Market) => void

  // 종목 목록
  stockList: StockConfig[]
  fetchStockList: () => Promise<void>
  addStock: (ticker: string, market: Market) => Promise<string>
  removeStock: (ticker: string, market: Market) => Promise<void>
}

export const useSignalStore = create<SignalStore>()(
  persist(
    (set, get) => ({
      // 인증
      isAuthenticated: false,
      authenticate: (password: string) => {
        const expected = process.env.NEXT_PUBLIC_ACCESS_PASSWORD || ""
        if (!expected || password === expected) {
          if (typeof window !== "undefined") {
            sessionStorage.setItem("access_token", password)
          }
          set({ isAuthenticated: true })
          return true
        }
        return false
      },

      // 탭
      activeTab: "portfolio",
      setActiveTab: (tab) => set({ activeTab: tab }),

      // 포트폴리오
      portfolio: [],
      portfolioLoading: false,
      portfolioError: null,
      portfolioTimestamp: null,
      fetchPortfolio: async () => {
        set({ portfolioLoading: true, portfolioError: null })
        try {
          const data = await api.getPortfolio()
          set({
            portfolio: data.stocks,
            portfolioTimestamp: data.generated_at,
            portfolioLoading: false,
          })
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : "오류 발생"
          if (msg === "unauthorized") set({ isAuthenticated: false })
          set({ portfolioError: msg, portfolioLoading: false })
        }
      },

      // 개별 종목
      selectedTicker: null,
      selectedMarket: null,
      result: null,
      loading: false,
      error: null,
      fetchSignal: async (ticker, market) => {
        set({ loading: true, error: null, selectedTicker: ticker, selectedMarket: market })
        try {
          const data = await api.getSignal(ticker, market)
          set({ result: data, loading: false })
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : "오류 발생"
          if (msg === "unauthorized") set({ isAuthenticated: false })
          set({ error: msg, loading: false })
        }
      },
      selectFromPortfolio: (ticker, market) => {
        set({ activeTab: "detail", selectedTicker: ticker, selectedMarket: market, result: null })
        get().fetchSignal(ticker, market)
      },

      // 종목 목록
      stockList: [],
      fetchStockList: async () => {
        try {
          const data = await api.getStocks()
          set({ stockList: data })
        } catch {
          // 무시
        }
      },
      addStock: async (ticker, market) => {
        const res = await api.addStock(ticker, market)
        await get().fetchStockList()
        return res.name
      },
      removeStock: async (ticker, market) => {
        await api.removeStock(ticker, market)
        await get().fetchStockList()
        // 포트폴리오 목록에서도 즉시 제거
        set((s) => ({
          portfolio: s.portfolio.filter(
            (p) => !(p.ticker === ticker && p.market === market)
          ),
        }))
      },
    }),
    {
      name: "signal-store",
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        activeTab: state.activeTab,
      }),
    }
  )
)
