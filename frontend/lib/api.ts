import type { PortfolioResponse, Recommendation, SignalResult, StockConfig } from "@/types"

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5000"

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getSignal: (ticker: string, market: string) =>
    apiFetch<SignalResult>(`/api/signal?ticker=${ticker}&market=${market}`),

  getPortfolio: () =>
    apiFetch<PortfolioResponse>("/api/portfolio"),

  getStocks: () =>
    apiFetch<StockConfig[]>("/api/stocks"),

  addStock: (ticker: string, market: string) =>
    apiFetch<{ ok: boolean; ticker: string; market: string; name: string }>("/api/stocks", {
      method: "POST",
      body: JSON.stringify({ ticker, market }),
    }),

  removeStock: (ticker: string, market: string) =>
    apiFetch<{ ok: boolean }>(`/api/stocks/${market}/${ticker}`, {
      method: "DELETE",
    }),

  refreshCache: (ticker: string, market: string) =>
    apiFetch("/api/refresh-cache", {
      method: "POST",
      body: JSON.stringify({ ticker, market }),
    }),

  getRecommendation: () =>
    apiFetch<Recommendation>("/api/recommendation"),

  searchStocks: (q: string, market: string) =>
    apiFetch<{ ticker: string; name: string; market: string }[]>(
      `/api/stocks/search?q=${encodeURIComponent(q)}&market=${market}`
    ),
}
