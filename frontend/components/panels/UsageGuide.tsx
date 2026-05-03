export default function UsageGuide() {
  return (
    <div className="space-y-4 max-w-3xl">

      {/* 개요 */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h2 className="text-base font-bold text-blue-800 mb-1">이 대시보드란?</h2>
        <p className="text-sm text-blue-700">
          보유 종목의 <strong>매수·매도 신호를 0~100점</strong>으로 수치화해 아침마다 포트폴리오 우선순위를 한눈에 확인하는 도구입니다.
          기술 지표·기관 흐름·AI 뉴스 감성을 합산해 점수를 냅니다.
        </p>
      </div>

      {/* 탭 구성 */}
      <Section title="화면 구성 — 탭별 역할">
        <Row icon="📋" label="전체 포트폴리오" desc="등록한 모든 종목의 매수/매도 점수를 한 화면에서 비교. 매일 아침 여기부터 확인하세요." />
        <Row icon="🤖" label="AI 추천" desc="Gemini AI가 포트폴리오 데이터를 읽고 오늘 주목할 매수·매도 후보를 글로 정리해줍니다." />
        <Row icon="📊" label="신호 검증" desc="특정 종목의 과거 매수 신호가 실제로 수익을 냈는지 백테스트로 확인합니다." />
        <Row icon="🔍" label="개별 종목 분석" desc="종목을 선택하면 매수·매도 신호 20개의 세부 점수와 뉴스 감성을 상세히 봅니다." />
        <Row icon="📖" label="지표 가이드" desc="RSI, MACD 등 20개 기술 지표의 의미와 계산 방식을 설명합니다." />
      </Section>

      {/* 점수 읽기 */}
      <Section title="점수·신호 배지 읽는 법">
        <p className="text-sm text-gray-600 mb-3">
          매수·매도 점수는 각각 <strong>0~100점</strong>. 두 점수는 독립적입니다 (매수 70점이어도 매도 40점일 수 있음).
        </p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <ScoreBadge color="bg-emerald-100 text-emerald-700 border border-emerald-300" label="▲ 강한 매수" range="86~100점" />
          <ScoreBadge color="bg-emerald-50 text-emerald-500" label="▲ 매수" range="71~85점" />
          <ScoreBadge color="bg-red-100 text-red-700 border border-red-300" label="▼ 강한 매도" range="86~100점" />
          <ScoreBadge color="bg-red-50 text-red-400" label="▼ 매도" range="71~85점" />
        </div>
        <p className="text-xs text-gray-400 mt-2">
          51~70점 = moderate(표시 안 됨) · 31~50점 = weak · 0~30점 = 중립
        </p>
        <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-xs text-yellow-700">
          ★ 별표는 <strong>컨플루언스 보너스</strong> — 6개 지표 카테고리 중 4개 이상 동시에 신호가 켜질 때 +10점 추가됩니다.
        </div>
      </Section>

      {/* 종목 관리 */}
      <Section title="종목 추가·삭제">
        <ol className="text-sm text-gray-700 space-y-2 list-decimal list-inside">
          <li>
            <strong>전체 포트폴리오</strong> 탭 우측 상단의 <strong>종목 관리</strong> 버튼을 누릅니다.
          </li>
          <li>
            입력창에 <strong>한글 종목명</strong>(예: 삼성전자)을 치면 자동완성 드롭다운이 나타납니다. 원하는 종목을 클릭하면 티커가 채워집니다.
          </li>
          <li>
            미국 주식은 티커를 직접 입력하고 시장을 <strong>미국(US)</strong>으로 바꾼 뒤 추가합니다.
          </li>
          <li>
            추가 후 <strong>새로고침</strong> 버튼을 눌러야 점수가 계산됩니다.
          </li>
          <li>
            삭제는 종목 행에 마우스를 올리면 오른쪽에 <strong>삭제</strong> 버튼이 나타납니다.
          </li>
        </ol>
      </Section>

      {/* 단타 적합도 */}
      <Section title="단타 적합도 배지">
        <p className="text-sm text-gray-600 mb-2">
          ATR(평균 변동폭)을 기준으로 그날 단타에 적합한 종목인지 표시합니다.
        </p>
        <div className="flex flex-wrap gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">고변동 (단타 적합)</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 border border-yellow-200">중변동</span>
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 border border-gray-200">저변동 (단타 비적합)</span>
        </div>
      </Section>

      {/* 갱신 주기 */}
      <Section title="데이터 갱신 주기">
        <div className="text-sm text-gray-700 space-y-1">
          <p>· 포트폴리오 화면은 <strong>5분마다 자동 갱신</strong>됩니다 (수동 새로고침도 가능).</p>
          <p>· 주가·기술 지표: 15분 캐시 · 기관/외국인: 30분 · 뉴스: 60분 · AI 감성: 120분</p>
          <p>· 장 마감 후·주말에는 <strong>마지막 거래일 데이터</strong>로 표시됩니다.</p>
          <p>· 미국 주식은 기관/외국인 데이터가 없어 해당 항목 점수는 타 지표로 재분배됩니다.</p>
        </div>
      </Section>

      {/* 주의사항 */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-xs text-gray-500">
        <strong className="text-gray-600">주의</strong> — 이 대시보드는 투자 참고용 보조 도구입니다.
        점수가 높다고 반드시 상승하지 않으며, 최종 매매 판단은 본인 책임입니다.
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-bold text-gray-700 mb-3">{title}</h3>
      {children}
    </div>
  )
}

function Row({ icon, label, desc }: { icon: string; label: string; desc: string }) {
  return (
    <div className="flex items-start gap-2 py-1.5 border-b border-gray-50 last:border-0">
      <span className="text-base leading-5">{icon}</span>
      <div>
        <span className="text-sm font-semibold text-gray-800">{label}</span>
        <span className="text-sm text-gray-500"> — {desc}</span>
      </div>
    </div>
  )
}

function ScoreBadge({ color, label, range }: { color: string; label: string; range: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${color}`}>{label}</span>
      <span className="text-xs text-gray-400">{range}</span>
    </div>
  )
}
