# 개발 가이드라인 & 교훈

## 배포 환경

| 구성 | URL |
|------|-----|
| 백엔드 (Railway) | `https://stock-signal-production.up.railway.app` |
| 프론트엔드 (Vercel) | `https://stock-signal-chi.vercel.app` |
| GitHub | `https://github.com/yellowbird627-hh/stock-signal` |

---

## 코드 규칙

### Python (백엔드)

- `load_dotenv()`는 반드시 서비스 모듈 import **전**에 호출  
  → 순서가 바뀌면 `GEMINI_API_KEY` 등 환경변수가 빈 문자열로 초기화됨

- scorer.py의 신호 데이터는 반드시 구조화된 dict로 관리  
  ```python
  # 올바른 방식
  _sig(score, max_score, detail)  # → {"score": x, "max": y, "detail": z}
  
  # 금지: flat 키 방식
  b["b1"] = 25
  b["b1_detail"] = "..."
  b["b1_max"] = 25
  ```

- pykrx 등 외부 라이브러리는 함수 내부가 아닌 모듈 상단에서 import

- KRX API는 주말/공휴일에 공매도·투자자 데이터를 제공하지 않음  
  → `backend/data/flow_cache/`에 마지막 거래일 데이터를 파일로 보관하는 방식으로 대응

### TypeScript (프론트엔드)

- 계산한 변수는 반드시 사용할 것 (미사용 변수 선언 금지)
- 인증 로직은 제거됨 — `isAuthenticated`, `authenticate`, `X-Access-Token` 관련 코드 추가 금지

---

## 배포 시 주의사항

### Railway (백엔드)

- **Root Directory**: `backend`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
- **필수 환경변수**:
  - `GEMINI_API_KEY` — Google AI Studio에서 발급
  - `FRONTEND_ORIGIN` — `*` (또는 Vercel URL)
- **`ACCESS_PASSWORD`는 설정하지 말 것** — 설정 시 프론트엔드 요청이 전부 401로 차단됨
- Railway가 `PORT` 환경변수를 자동 주입하므로 수동으로 `PORT` 설정 불필요

### Vercel (프론트엔드)

- **Root Directory**: `frontend` — 반드시 설정 (누락 시 403 Forbidden 발생)
- **Deployment Protection**: 반드시 비활성화 (기본값이 활성화로 켜져 있어 외부 접근 차단)
- 환경변수 Key 이름에 공백이 들어가면 "invalid" 오류 → 저장 전 확인
- 환경변수 변경 후 반드시 **Redeploy** 해야 반영됨
- **필수 환경변수**:
  - `NEXT_PUBLIC_BACKEND_URL` — Railway URL (예: `https://stock-signal-production.up.railway.app`)

### GitHub

- `frontend/.git` 이 존재하면 서브모듈 충돌 발생  
  → `git rm --cached frontend && rm -rf frontend/.git` 로 제거

---

## AI API

- **사용 모델**: `gemini-2.5-flash` (Google Gemini)
- **패키지**: `google-genai` (`from google import genai`) — `google-generativeai`는 deprecated
- `gemini-2.0-flash`는 신규 사용자에게 비활성화됨 → `gemini-2.5-flash` 사용

---

## 로컬 개발

```bash
# 백엔드 (포트 5100)
cd backend && python app.py

# 프론트엔드 (포트 3001 — 3000은 macOS ControlCenter, 5000은 AirPlay가 점유)
cd frontend && npm run dev -- -p 3001
```

포트 충돌 시:
```bash
lsof -ti :5100 | xargs kill -9
```

## 코드 변경 후 배포

```bash
git add <파일>
git commit -m "설명"
git push origin main
# → Railway·Vercel이 자동 재배포
```
