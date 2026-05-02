import type { Suitability } from "@/types"

const CONFIG: Record<Suitability, { label: string; color: string; desc: string }> = {
  high:   { label: "단타 적합", color: "bg-emerald-100 text-emerald-800 border-emerald-300", desc: "변동성 충분" },
  medium: { label: "보통",     color: "bg-yellow-100 text-yellow-800 border-yellow-300",   desc: "평균 변동성" },
  low:    { label: "단타 비추", color: "bg-stone-100 text-stone-600 border-stone-300",     desc: "변동성 낮음" },
}

export default function TradingSuitability({
  suitability, atrPct,
}: { suitability: Suitability; atrPct: number }) {
  const cfg = CONFIG[suitability]
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${cfg.color}`}>
      {cfg.label}
      <span className="opacity-60">ATR {atrPct}%</span>
    </span>
  )
}
