# 주식 트렌드 예측 에이전트 - Frontend

React + Vite + Tailwind CSS로 구성된 프론트엔드 프로젝트입니다.

## 📁 프로젝트 구조

```
stock-trend-frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── .env
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── index.css
    ├── api/
    │   ├── axios.js
    │   ├── newsApi.js
    │   └── stocksApi.js
    ├── components/
    │   ├── Navbar.jsx
    │   ├── NewsCard.jsx
    │   └── StockChart.jsx
    └── pages/
        ├── Dashboard.jsx
        ├── AllNews.jsx
        ├── SectorNews.jsx
        └── SectorStocks.jsx
```

## 🚀 시작하기

### 1. 프로젝트 폴더 생성
```bash
mkdir stock-trend-frontend
cd stock-trend-frontend
```

### 2. 파일 배치
다운로드한 19개 파일을 다음과 같이 배치하세요:

**루트 폴더에 배치:**
- package.json
- vite.config.js
- tailwind.config.js
- postcss.config.js
- index.html
- .env

**src/ 폴더 생성 후 배치:**
- src/main.jsx
- src/App.jsx
- src/index.css

**src/api/ 폴더 생성 후 배치:**
- src/api/axios.js
- src/api/newsApi.js
- src/api/stocksApi.js

**src/components/ 폴더 생성 후 배치:**
- src/components/Navbar.jsx
- src/components/NewsCard.jsx
- src/components/StockChart.jsx

**src/pages/ 폴더 생성 후 배치:**
- src/pages/Dashboard.jsx
- src/pages/AllNews.jsx
- src/pages/SectorNews.jsx
- src/pages/SectorStocks.jsx

### 3. 패키지 설치
```bash
npm install
```

### 4. 개발 서버 실행
```bash
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

## ⚙️ 환경 설정

`.env` 파일에서 백엔드 API URL 설정:
```
VITE_API_URL=http://localhost:8000
```

## 📱 주요 기능

### 1. 대시보드 (`/`)
- 섹터별 시장 감성 온도 표시
- 긍정/중립/부정 뉴스 개수 통계
- 섹터별 뉴스/주식 바로가기

### 2. 전체 뉴스 (`/news`)
- 모든 섹터의 뉴스 보기
- 섹터별 필터링
- AI 감성 분석 트리거

### 3. 섹터별 뉴스 (`/sector/:id/news`)
- 특정 섹터의 뉴스 목록
- 뉴스 수집 기능

### 4. 섹터별 주식 (`/sector/:id/stocks`)
- 주가 차트 (Recharts)
- 기간 선택 (7일/30일/90일)
- 주가 데이터 수집 기능

## 🔗 백엔드 연동

백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 합니다.

### 백엔드 API 엔드포인트
- `GET /news/sectors` - 섹터 목록
- `GET /news/dashboard-summary` - 대시보드 통계
- `GET /news/sector/{id}` - 섹터별 뉴스
- `GET /news/` - 전체 뉴스
- `POST /news/collect` - 뉴스 수집
- `POST /news/analyze` - AI 감성 분석
- `GET /stocks/sector/{id}` - 섹터별 주식
- `POST /stocks/collect` - 주가 수집

## 🎨 기술 스택

- **React 18** - UI 라이브러리
- **Vite** - 빌드 도구
- **React Router** - 라우팅
- **Axios** - HTTP 클라이언트
- **Tailwind CSS** - 스타일링
- **Recharts** - 차트 라이브러리

## 📦 빌드

프로덕션 빌드:
```bash
npm run build
```

빌드 결과물 미리보기:
```bash
npm run preview
```

## 🐛 문제 해결

### 백엔드 연결 안 될 때
1. 백엔드 서버 실행 확인: `http://localhost:8000`
2. `.env` 파일의 `VITE_API_URL` 확인
3. 브라우저 콘솔에서 CORS 에러 확인

### 빌드 에러 날 때
```bash
rm -rf node_modules package-lock.json
npm install
```
