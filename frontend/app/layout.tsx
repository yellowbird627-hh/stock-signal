import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "주식 매매 신호 대시보드",
  description: "한국/미국 대형주 단타 매수·매도 신호 분석",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className="h-full">
      <body className="min-h-full bg-slate-50">{children}</body>
    </html>
  )
}
