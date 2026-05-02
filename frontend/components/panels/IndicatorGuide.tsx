const BUY_INDICATORS = [
  {
    name: "기관+외국인 순매수",
    code: "B1",
    max: 25,
    trigger: "기관과 외국인이 동시에 3일 이상 연속 순매수",
    meaning: "대규모 자금을 운용하는 기관투자자와 외국인이 함께 사는 종목은 상승 확률이 높습니다. 둘 다 팔 때는 하락 위험이 큽니다.",
    example: "예: 기관 3일 연속 +200억, 외국인 3일 연속 +100억 → 25점 만점",
    tip: "한 쪽만 사는 경우보다 둘이 동시에 사는 경우가 훨씬 강한 신호입니다.",
    color: "emerald",
  },
  {
    name: "고점 대비 하락",
    code: "B2",
    max: 15,
    trigger: "최근 30일 고점 대비 10% 이상 하락",
    meaning: "주가가 충분히 내려왔을 때 반등을 노리는 전략입니다. 단, 하락이 기업 문제가 아닌 시장 조정인지 확인이 필요합니다.",
    example: "예: 30일 고점 10만원 → 현재 8.5만원(-15%) → 15점 만점",
    tip: "5~10% 하락은 8점, 10% 이상 하락은 15점. 뉴스 신호와 함께 보면 더 신뢰도 높아집니다.",
    color: "emerald",
  },
  {
    name: "긍정 뉴스",
    code: "B3",
    max: 15,
    trigger: "AI 뉴스 감성 점수 0.6 이상 (1.0이 최고 긍정)",
    meaning: "최근 뉴스가 호재 중심일 때 주가 상승 기대감이 높아집니다. 실적 서프라이즈, 수주, 신제품 출시 등이 해당됩니다.",
    example: "예: '삼성전자 2분기 영업이익 전망 상회' → 감성 0.8 → 12점",
    tip: "뉴스는 이미 반영된 경우도 있으니 다른 지표와 함께 확인하세요.",
    color: "emerald",
  },
  {
    name: "RSI 과매도",
    code: "B4",
    max: 10,
    trigger: "RSI 35 미만 (과매도 구간)",
    meaning: "RSI(상대강도지수)는 0~100 사이 값으로, 30 이하면 '너무 많이 팔렸다'는 신호입니다. 반등 가능성이 높아집니다.",
    example: "예: RSI 28 → 10점 만점 / RSI 42 → 5점 / RSI 55 → 0점",
    tip: "RSI 단독으로는 오신호가 많습니다. MACD나 볼린저밴드와 함께 볼 때 신뢰도가 올라갑니다.",
    color: "emerald",
  },
  {
    name: "MACD 골든크로스",
    code: "B5",
    max: 8,
    trigger: "MACD선이 시그널선을 아래에서 위로 교차",
    meaning: "MACD는 단기 이동평균과 장기 이동평균의 차이입니다. 골든크로스는 단기 추세가 장기 추세를 상향 돌파하는 시점으로 상승 전환 신호입니다.",
    example: "예: 어제까지 MACD -0.3 < 시그널 -0.1, 오늘 MACD 0.1 > 시그널 0.05 → 8점",
    tip: "크로스 발생 직후 진입하는 게 이상적입니다. 발생 후 2~3일 이내가 최적 진입 구간입니다.",
    color: "emerald",
  },
  {
    name: "거래량 급증+양봉",
    code: "B6",
    max: 5,
    trigger: "거래량이 전일 대비 2배 이상이면서 양봉(상승 마감)",
    meaning: "많은 사람이 사면서 주가가 올랐다는 의미입니다. 강한 매수세 진입을 나타내며 추가 상승 기대감이 높습니다.",
    example: "예: 전일 거래량 100만주, 오늘 230만주 + 양봉 → 5점",
    tip: "거래량 없는 상승은 약한 신호입니다. 거래량 급증+양봉은 단타에서 가장 직관적인 매수 신호입니다.",
    color: "emerald",
  },
  {
    name: "볼린저 하단",
    code: "B7",
    max: 8,
    trigger: "주가가 볼린저밴드 하단 근처이거나 이탈 후 복귀",
    meaning: "볼린저밴드는 주가의 정상 움직임 범위를 나타냅니다. 하단 이탈은 과도한 하락, 복귀는 정상 범위로 돌아오는 반등 신호입니다.",
    example: "예: 볼린저 하단 8만원, 주가 7.9만원으로 이탈 후 8.1만원 복귀 → 8점",
    tip: "하단 터치(4점)보다 이탈 후 복귀(8점)가 더 강한 신호입니다. 복귀는 반등 확인을 의미합니다.",
    color: "emerald",
  },
  {
    name: "스토캐스틱 과매도",
    code: "B8",
    max: 7,
    trigger: "스토캐스틱 K값 20 미만 + 상향 크로스",
    meaning: "스토캐스틱은 최근 가격 범위에서 현재 가격의 위치를 0~100으로 나타냅니다. 20 미만은 바닥권으로 반등 가능성이 높습니다.",
    example: "예: K=15, D=18, K가 D를 상향 돌파 → 7점 / K=15만 충족(크로스 없음) → 3점",
    tip: "RSI와 비슷한 역할을 하지만 더 민감합니다. 단타에서 빠른 진입 타이밍을 잡는 데 유용합니다.",
    color: "emerald",
  },
  {
    name: "공매도 감소",
    code: "B9",
    max: 4,
    trigger: "공매도 비율이 연속으로 감소하는 추세",
    meaning: "공매도는 주가 하락에 베팅하는 투자입니다. 공매도 비율 감소는 하락 베팅 세력이 줄어드는 것으로 매수 신호입니다.",
    example: "예: 공매도 비율 5%→4.2%→3.8% (2일 연속 감소) → 4점",
    tip: "한국 주식 전용 지표입니다. 공매도 세력은 기업 내부 정보에 접근하는 경우가 많아 주목할 필요가 있습니다.",
    color: "emerald",
  },
  {
    name: "이평선 정배열",
    code: "B10",
    max: 3,
    trigger: "5일 > 20일 > 60일 이동평균선 순서 유지",
    meaning: "단기, 중기, 장기 이동평균선이 정배열되면 모든 기간의 추세가 상승 방향임을 의미합니다. 가장 안정적인 상승 추세 확인 지표입니다.",
    example: "예: 5일선 10.2만 > 20일선 9.8만 > 60일선 9.2만 → 완전 정배열 3점",
    tip: "정배열은 확인 지표입니다. 이미 많이 오른 상태일 수 있으니 다른 신호와 함께 봐야 합니다.",
    color: "emerald",
  },
]

const SELL_INDICATORS = [
  {
    name: "기관+외국인 순매도",
    code: "S1",
    max: 25,
    trigger: "기관과 외국인이 동시에 3일 이상 연속 순매도",
    meaning: "큰손들이 함께 팔기 시작하면 주가 하락 압력이 강해집니다. 이 신호가 지속되면 추가 하락 위험이 높습니다.",
    example: "예: 기관 3일 연속 -150억, 외국인 3일 연속 -80억 → 25점",
    tip: "매수 B1 지표의 반대입니다. 둘 중 하나만 팔 때보다 동반 매도가 훨씬 위험합니다.",
    color: "red",
  },
  {
    name: "저점 대비 상승",
    code: "S2",
    max: 15,
    trigger: "최근 30일 저점 대비 30% 이상 상승",
    meaning: "단기간에 많이 오른 주식은 차익실현 매물 압력이 높아집니다. 30% 이상 상승 후에는 조정 리스크를 고려해야 합니다.",
    example: "예: 30일 저점 8만원 → 현재 11만원(+37.5%) → 15점",
    tip: "상승폭이 클수록 점수가 높습니다. 모멘텀이 강한 종목은 더 오를 수도 있으니 다른 신호와 종합 판단하세요.",
    color: "red",
  },
  {
    name: "부정 뉴스",
    code: "S3",
    max: 15,
    trigger: "AI 뉴스 감성 점수 0.4 이하 (부정)",
    meaning: "실적 쇼크, 규제 리스크, 경영 문제 등 악재 뉴스가 많을 때 주가 하락 위험이 높습니다.",
    example: "예: '반도체 수요 둔화 우려, 실적 하향 전망' → 감성 0.2 → 12점",
    tip: "뉴스 악재는 이미 주가에 반영됐을 수도 있습니다. 최근 주가 흐름과 함께 확인하세요.",
    color: "red",
  },
  {
    name: "RSI 과매수",
    code: "S4",
    max: 10,
    trigger: "RSI 65 초과 (과매수 구간)",
    meaning: "RSI가 70 이상이면 '너무 많이 올랐다'는 신호입니다. 단기 조정 가능성이 높아집니다.",
    example: "예: RSI 78 → 10점 / RSI 68 → 5점 / RSI 55 → 0점",
    tip: "RSI 과매수 상태에서도 강한 상승 추세면 계속 오를 수 있습니다. 추세 꺾임(MACD 데드크로스 등)과 함께 보세요.",
    color: "red",
  },
  {
    name: "MACD 데드크로스",
    code: "S5",
    max: 8,
    trigger: "MACD선이 시그널선을 위에서 아래로 교차",
    meaning: "골든크로스의 반대입니다. 단기 추세가 장기 추세를 하향 돌파하는 시점으로 하락 전환 신호입니다.",
    example: "예: 어제 MACD 0.3 > 시그널 0.1, 오늘 MACD 0.05 < 시그널 0.08 → 8점",
    tip: "데드크로스 발생 후 2~3일 내 매도가 이상적입니다.",
    color: "red",
  },
  {
    name: "거래량 급증+음봉",
    code: "S6",
    max: 5,
    trigger: "거래량이 전일 대비 2배 이상이면서 음봉(하락 마감)",
    meaning: "많은 사람이 팔면서 주가가 내렸다는 의미입니다. 강한 매도세 진입을 나타냅니다.",
    example: "예: 전일 거래량 100만주, 오늘 250만주 + 음봉 → 5점",
    tip: "대량 거래 음봉은 세력 이탈 또는 악재 소화의 신호일 수 있습니다.",
    color: "red",
  },
  {
    name: "볼린저 상단",
    code: "S7",
    max: 8,
    trigger: "주가가 볼린저밴드 상단 근처이거나 이탈 후 복귀",
    meaning: "볼린저밴드 상단 이탈은 과도한 상승을 의미합니다. 정상 범위로 복귀하는 과정에서 하락합니다.",
    example: "예: 볼린저 상단 11만원, 주가 11.3만원 이탈 후 10.8만원 복귀 → 8점",
    tip: "상단 터치(4점)보다 이탈 후 복귀(8점)가 더 강한 매도 신호입니다.",
    color: "red",
  },
  {
    name: "스토캐스틱 과매수",
    code: "S8",
    max: 7,
    trigger: "스토캐스틱 K값 80 초과 + 하향 크로스",
    meaning: "스토캐스틱이 80 이상이면 고가 영역에서 과열 상태입니다. 하향 크로스는 조정 시작을 의미합니다.",
    example: "예: K=85, D=82, K가 D를 하향 돌파 → 7점",
    tip: "과매수 상태에서 하향 크로스가 발생하면 단기 급락 가능성이 높습니다.",
    color: "red",
  },
  {
    name: "공매도 급증",
    code: "S9",
    max: 4,
    trigger: "공매도 비율이 연속으로 증가하는 추세",
    meaning: "하락에 베팅하는 세력이 늘어나는 것입니다. 기관이나 헤지펀드가 하락을 예상하고 있다는 의미입니다.",
    example: "예: 공매도 비율 2%→3.1%→4.5% (2일 연속 증가) → 4점",
    tip: "공매도 급증은 미래 하락 압력을 예고합니다. 특히 코스피 대형주에서 의미 있는 신호입니다.",
    color: "red",
  },
  {
    name: "이평선 역배열",
    code: "S10",
    max: 3,
    trigger: "5일 < 20일 < 60일 이동평균선 순서",
    meaning: "단기, 중기, 장기 모두 하락 추세임을 의미합니다. 모든 기간의 투자자가 손실 구간에 있어 반등하면 팔려는 압력이 강합니다.",
    example: "예: 5일선 9.2만 < 20일선 9.8만 < 60일선 10.5만 → 완전 역배열 3점",
    tip: "역배열은 추세 악화를 확인하는 지표입니다. 역배열 중 반등은 매도 기회가 될 수 있습니다.",
    color: "red",
  },
]

function IndicatorCard({ ind, side }: { ind: typeof BUY_INDICATORS[0]; side: "buy" | "sell" }) {
  const c = side === "buy" ? "emerald" : "red"
  const border = side === "buy" ? "border-emerald-100" : "border-red-100"
  const badge = side === "buy" ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
  const title = side === "buy" ? "text-emerald-700" : "text-red-700"
  const tipBg = side === "buy" ? "bg-emerald-50 text-emerald-800" : "bg-red-50 text-red-800"

  return (
    <div className={`bg-white rounded-xl border ${border} p-4 space-y-2.5`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono font-bold px-1.5 py-0.5 rounded ${badge}`}>{ind.code}</span>
          <span className={`font-semibold text-sm ${title}`}>{ind.name}</span>
        </div>
        <span className="text-xs text-gray-400 font-mono">최대 {ind.max}점</span>
      </div>

      <div>
        <p className="text-xs font-semibold text-gray-500 mb-0.5">발동 조건</p>
        <p className="text-xs text-gray-700">{ind.trigger}</p>
      </div>

      <div>
        <p className="text-xs font-semibold text-gray-500 mb-0.5">의미</p>
        <p className="text-xs text-gray-700 leading-relaxed">{ind.meaning}</p>
      </div>

      <div>
        <p className="text-xs font-semibold text-gray-500 mb-0.5">예시</p>
        <p className="text-xs text-gray-600 italic">{ind.example}</p>
      </div>

      <div className={`rounded-lg px-3 py-2 text-xs leading-relaxed ${tipBg}`}>
        💡 {ind.tip}
      </div>
    </div>
  )
}

export default function IndicatorGuide() {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-lg font-bold text-gray-800">지표 가이드</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          매수·매도 신호에 사용되는 20개 지표의 의미와 해석 방법을 설명합니다
        </p>
      </div>

      {/* 점수 체계 설명 */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-2">
        <p className="text-sm font-bold text-blue-800">📊 점수 체계</p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
          {[
            { range: "0~30점", label: "신호 없음", color: "text-gray-500" },
            { range: "31~50점", label: "약한 신호", color: "text-yellow-600" },
            { range: "51~70점", label: "보통 신호", color: "text-orange-500" },
            { range: "71~85점", label: "강한 신호", color: "text-emerald-600" },
            { range: "86~100점", label: "매우 강한 신호", color: "text-emerald-700 font-bold" },
          ].map((s) => (
            <div key={s.range} className="bg-white rounded-lg px-2 py-1.5 text-center border border-blue-100">
              <div className={`font-semibold ${s.color}`}>{s.range}</div>
              <div className="text-gray-500">{s.label}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-blue-700">
          ★ 컨플루언스 보너스: 6개 카테고리(기관흐름·가격위치·뉴스·오실레이터·추세·거래량) 중 4개 이상 동시 충족 시 +10점
        </p>
      </div>

      {/* 매수 지표 */}
      <div>
        <h3 className="text-base font-bold text-emerald-700 mb-4 flex items-center gap-2">
          <span className="w-6 h-6 bg-emerald-600 text-white rounded-full flex items-center justify-center text-xs">▲</span>
          매수 신호 지표 (B1~B10)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {BUY_INDICATORS.map((ind) => (
            <IndicatorCard key={ind.code} ind={ind} side="buy" />
          ))}
        </div>
      </div>

      {/* 매도 지표 */}
      <div>
        <h3 className="text-base font-bold text-red-700 mb-4 flex items-center gap-2">
          <span className="w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center text-xs">▼</span>
          매도 신호 지표 (S1~S10)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SELL_INDICATORS.map((ind) => (
            <IndicatorCard key={ind.code} ind={ind} side="sell" />
          ))}
        </div>
      </div>
    </div>
  )
}
