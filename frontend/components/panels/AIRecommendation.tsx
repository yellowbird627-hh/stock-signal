"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import type { Recommendation } from "@/types"

export default function AIRecommendation() {
  const [data, setData] = useState<Recommendation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetch = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.getRecommendation()
      setData(res)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "오류 발생")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-800">AI 매매 추천</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            포트폴리오 전체 신호를 분석해 Claude가 매수·매도 종목과 타이밍을 추천합니다
          </p>
        </div>
        <button
          onClick={fetch}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {loading ? "분석 중..." : data ? "재분석" : "AI 분석 시작"}
        </button>
      </div>

      {/* 로딩 */}
      {loading && (
        <div className="text-center py-20 text-gray-400">
          <div className="text-4xl mb-3 animate-pulse">🤖</div>
          <p className="font-medium">포트폴리오 전체 신호 분석 중...</p>
          <p className="text-xs mt-1">Claude가 각 지표를 종합해 추천을 생성합니다</p>
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
          오류: {error}
        </div>
      )}

      {/* 결과 */}
      {data && !loading && (
        <div className="space-y-4">
          {/* 시장 요약 */}
          {data.summary && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-800">
              <span className="font-semibold mr-2">📊 시장 요약</span>
              {data.summary}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 매수 추천 */}
            <div>
              <h3 className="text-sm font-bold text-emerald-700 mb-3 flex items-center gap-1.5">
                <span className="w-5 h-5 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 text-xs">▲</span>
                매수 추천 {data.buy.length > 0 ? `(${data.buy.length}개)` : ""}
              </h3>
              {data.buy.length === 0 ? (
                <div className="text-center py-8 text-gray-400 bg-gray-50 rounded-xl border border-gray-100 text-sm">
                  현재 매수 추천 종목 없음
                </div>
              ) : (
                <div className="space-y-3">
                  {data.buy.map((item, i) => (
                    <div key={i} className="bg-white rounded-xl border border-emerald-200 p-4 space-y-2.5">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="font-bold text-gray-800">{item.name}</span>
                          <span className="ml-1.5 text-xs text-gray-400">{item.ticker}</span>
                        </div>
                        <span className="text-xs bg-emerald-600 text-white px-2 py-0.5 rounded-full font-medium shrink-0">
                          #{i + 1} 매수
                        </span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="text-xs font-semibold text-emerald-700 shrink-0 mt-0.5">⏰ 진입시점</span>
                        <span className="text-sm text-gray-700">{item.timing}</span>
                      </div>
                      <div className="flex items-start gap-2 bg-emerald-50 rounded-lg px-3 py-2">
                        <span className="text-xs font-semibold text-emerald-700 shrink-0 mt-0.5">📋 근거</span>
                        <span className="text-xs text-gray-700 leading-relaxed">{item.reason}</span>
                      </div>
                      {(item.target1 != null || item.target2 != null || item.stop_loss != null) && (
                        <div className="border-t border-emerald-100 pt-2 space-y-1">
                          {item.target1 != null && (
                            <div className="flex justify-between text-xs">
                              <span className="text-emerald-700 font-medium">🎯 1차 목표가</span>
                              <span className="font-mono font-semibold text-emerald-800">
                                {item.target1.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {item.target2 != null && (
                            <div className="flex justify-between text-xs">
                              <span className="text-emerald-700 font-medium">🎯 2차 목표가</span>
                              <span className="font-mono font-semibold text-emerald-800">
                                {item.target2.toLocaleString()}
                              </span>
                            </div>
                          )}
                          {item.stop_loss != null && (
                            <div className="flex justify-between text-xs">
                              <span className="text-red-600 font-medium">🛑 손절선</span>
                              <span className="font-mono font-semibold text-red-600">
                                {item.stop_loss.toLocaleString()}
                              </span>
                            </div>
                          )}
                          <p className="text-xs text-gray-400 pt-0.5">※ 기술적 참고치이며 투자 보장이 아닙니다</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 매도 추천 */}
            <div>
              <h3 className="text-sm font-bold text-red-700 mb-3 flex items-center gap-1.5">
                <span className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center text-red-600 text-xs">▼</span>
                매도 추천 {data.sell.length > 0 ? `(${data.sell.length}개)` : ""}
              </h3>
              {data.sell.length === 0 ? (
                <div className="text-center py-8 text-gray-400 bg-gray-50 rounded-xl border border-gray-100 text-sm">
                  현재 매도 추천 종목 없음
                </div>
              ) : (
                <div className="space-y-3">
                  {data.sell.map((item, i) => (
                    <div key={i} className="bg-white rounded-xl border border-red-200 p-4 space-y-2.5">
                      <div className="flex items-start justify-between">
                        <div>
                          <span className="font-bold text-gray-800">{item.name}</span>
                          <span className="ml-1.5 text-xs text-gray-400">{item.ticker}</span>
                        </div>
                        <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full font-medium shrink-0">
                          #{i + 1} 매도
                        </span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="text-xs font-semibold text-red-700 shrink-0 mt-0.5">⏰ 매도시점</span>
                        <span className="text-sm text-gray-700">{item.timing}</span>
                      </div>
                      <div className="flex items-start gap-2 bg-red-50 rounded-lg px-3 py-2">
                        <span className="text-xs font-semibold text-red-700 shrink-0 mt-0.5">📋 근거</span>
                        <span className="text-xs text-gray-700 leading-relaxed">{item.reason}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {data.generated_at && (
            <p className="text-xs text-gray-400 text-right">
              {new Date(data.generated_at).toLocaleString("ko-KR")} 분석
            </p>
          )}
        </div>
      )}

      {/* 초기 상태 */}
      {!data && !loading && !error && (
        <div className="text-center py-20 text-gray-400 bg-white rounded-xl border border-gray-100">
          <div className="text-5xl mb-4">🤖</div>
          <p className="font-medium text-gray-600 mb-1">AI 매매 추천</p>
          <p className="text-sm mb-5">포트폴리오 전체 신호를 종합해 매수·매도 종목과 진입 타이밍을 추천합니다</p>
          <button
            onClick={fetch}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
          >
            AI 분석 시작
          </button>
        </div>
      )}
    </div>
  )
}
