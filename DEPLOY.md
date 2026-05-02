# 배포 가이드 (Vercel + Railway)

## 1. 백엔드 — Railway 배포

### 1-1. Railway 계정 및 프로젝트 생성
1. railway.app 접속 → 회원가입 또는 로그인
2. "New Project" → "Deploy from GitHub repo" 선택
3. GitHub에 이 레포 push 후 연결, 또는 "Empty Project" → Railway CLI 사용

### 1-2. 환경변수 설정 (Railway 대시보드 Variables 탭)

| 변수명 | 값 |
|--------|-----|
| `ANTHROPIC_API_KEY` | Anthropic API 키 (console.anthropic.com) |
| `ACCESS_PASSWORD` | 두 사람이 공유할 비밀번호 (예: stock2024!) |
| `FRONTEND_ORIGIN` | 나중에 Vercel 배포 후 URL 입력 |

### 1-3. 배포
```bash
# Railway CLI 방법 (backend 폴더에서)
cd backend
railway login
railway up
```

배포 완료 후 Railway가 제공하는 URL을 복사해 둡니다.
(예: `https://stock-signal-backend-xxxxx.railway.app`)

---

## 2. 프론트엔드 — Vercel 배포

### 2-1. Vercel 계정 및 프로젝트 생성
1. vercel.com 접속 → 로그인
2. "New Project" → GitHub 레포 연결
3. **Root Directory**: `frontend` 로 설정 (중요!)

### 2-2. 환경변수 설정 (Vercel 대시보드 Settings → Environment Variables)

| 변수명 | 값 |
|--------|-----|
| `NEXT_PUBLIC_BACKEND_URL` | Railway에서 받은 백엔드 URL |
| `NEXT_PUBLIC_ACCESS_PASSWORD` | 백엔드와 동일한 비밀번호 |

### 2-3. 배포
Vercel이 자동으로 빌드·배포합니다.
배포 완료 후 Vercel URL을 복사합니다. (예: `https://stock-signal.vercel.app`)

---

## 3. CORS 업데이트

Railway 환경변수 `FRONTEND_ORIGIN`에 Vercel URL을 입력하고 재배포:
```
FRONTEND_ORIGIN=https://stock-signal.vercel.app
```

---

## 4. 공유 방법

상대방에게 이것만 알려주면 됩니다:
- **URL**: `https://stock-signal.vercel.app`
- **비밀번호**: 설정한 비밀번호

---

## 5. 종목 추가 방법

`backend/config/stocks.json` 파일에 종목 추가 후 Railway 재배포:

```json
{
  "version": "1.0",
  "stocks": [
    {"ticker": "005930", "market": "KRX", "name": "삼성전자", "enabled": true},
    {"ticker": "000660", "market": "KRX", "name": "SK하이닉스", "enabled": true},
    {"ticker": "035420", "market": "KRX", "name": "NAVER", "enabled": true},
    {"ticker": "AAPL",   "market": "US",  "name": "Apple",    "enabled": true},
    {"ticker": "NVDA",   "market": "US",  "name": "NVIDIA",   "enabled": true}
  ]
}
```

---

## 6. 로컬 개발 실행

### 백엔드
```bash
cd backend
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 입력
python3 app.py
# → http://localhost:5000
```

### 프론트엔드
```bash
cd frontend
# .env.local 파일이 이미 localhost:5000 으로 설정되어 있음
npm install
npm run dev
# → http://localhost:3000
```
