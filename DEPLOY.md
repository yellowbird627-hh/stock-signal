# 배포 가이드 (Railway + Vercel)

## 현재 배포 상태

| 구성 | URL |
|------|-----|
| 백엔드 | `https://stock-signal-production.up.railway.app` |
| 프론트엔드 | `https://stock-signal-chi.vercel.app` |

---

## 백엔드 — Railway

### 환경변수 (Variables 탭)

| 변수명 | 값 |
|--------|-----|
| `GEMINI_API_KEY` | Google AI Studio에서 발급한 키 |
| `FRONTEND_ORIGIN` | `*` |

> `ACCESS_PASSWORD`는 설정하지 말 것 — 설정 시 API 요청 전부 차단됨  
> `PORT`는 Railway가 자동 주입하므로 설정 불필요

### 설정 (Settings 탭)

- Root Directory: `backend`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`

---

## 프론트엔드 — Vercel

### 환경변수

| 변수명 | 값 |
|--------|-----|
| `NEXT_PUBLIC_BACKEND_URL` | Railway 백엔드 URL |

### 설정

- Root Directory: `frontend`
- Deployment Protection: **비활성화** (활성화 시 외부 접근 차단)

---

## 코드 변경 후 재배포

```bash
git add <변경된 파일>
git commit -m "변경 내용 설명"
git push origin main
```

push 후 Railway·Vercel이 자동으로 재배포합니다.

---

## 로컬 실행

```bash
# 백엔드
cd backend && python app.py   # → http://localhost:5100

# 프론트엔드
cd frontend && npm run dev -- -p 3001   # → http://localhost:3001
```

---

## 종목 추가/삭제

대시보드 UI의 **종목 관리** 버튼 사용 (코드 수정 불필요).  
또는 `backend/config/stocks.json` 직접 편집 후 push.
