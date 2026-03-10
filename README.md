# 📋 인사·동정·부고 뉴스 수집 봇

연합뉴스·한국경제의 인사/동정/부고 뉴스를 자동 수집하여  
텔레그램으로 전송하고 React 대시보드로 조회하는 시스템입니다.

---

## 🗂 프로젝트 구조

```
personnel-news-bot/
├── crawler/
│   ├── crawlers/
│   │   ├── base.py          # 베이스 크롤러 & NewsItem 모델
│   │   ├── yna.py           # 연합뉴스 크롤러
│   │   └── hankyung.py      # 한국경제 크롤러
│   ├── bot/
│   │   └── telegram_bot.py  # 텔레그램 전송 모듈
│   ├── db/
│   │   └── models.py        # MariaDB CRUD (중복 제거 포함)
│   ├── scheduler/
│   │   └── scheduler.py     # APScheduler 주기 실행
│   ├── main.py              # 파이프라인 진입점
│   ├── requirements.txt
│   └── Dockerfile
├── backend/
│   └── app.py               # FastAPI REST API
├── frontend/
│   └── src/
│       ├── App.jsx           # 메인 앱
│       └── components/
│           ├── NewsCard.jsx  # 뉴스 카드
│           ├── FilterBar.jsx # 필터 (카테고리/소스)
│           ├── StatsPanel.jsx# 통계 패널
│           └── NewsModal.jsx # 상세 모달 (공유 기능)
├── docker-compose.yml
└── .env.example
```

---

## 🚀 단계별 실행 방법

### 1단계 — MVP: 텔레그램 봇 (DB 없이)

```bash
cd crawler
pip install -r requirements.txt

# .env 파일 생성
cp ../.env.example ../.env
# TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 입력

# DB 없이 바로 텔레그램 전송
python main.py --no-db
```

### 2단계 — DB 구축 + 중복 제거

```bash
# MariaDB 실행 (Docker)
docker-compose up -d db

# .env에서 DB 정보 설정 후
python main.py   # DB 저장 + 텔레그램 전송

# 주기적 실행 (1시간마다)
python scheduler/scheduler.py
```

### 3단계 — React 대시보드

```bash
# 전체 스택 Docker 실행
docker-compose up -d

# 접속
# 대시보드: http://localhost:3000
# API:      http://localhost:8000/docs
```

---

## ⚙️ 환경변수 설정

`.env.example`을 복사하여 `.env`로 저장 후 값을 입력합니다.

| 변수 | 설명 | 예시 |
|------|------|------|
| `TELEGRAM_BOT_TOKEN` | BotFather에서 발급받은 토큰 | `123456:ABC-...` |
| `TELEGRAM_CHAT_ID` | 전송할 채팅/그룹/채널 ID | `-1001234567890` |
| `DB_HOST` | MariaDB 호스트 | `localhost` |
| `CRON_HOUR` | 크롤링 주기(시간) | `*/1` (매시간) |

### 텔레그램 봇·채팅 ID 확인 방법

1. **봇 생성**: `@BotFather` → `/newbot` → 토큰 발급
2. **채팅 ID**: `@userinfobot` 에게 메시지 → ID 확인
3. **그룹/채널**: 봇을 관리자로 추가 → `https://api.telegram.org/bot<TOKEN>/getUpdates` 에서 `chat.id` 확인

---

## 📡 API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/news` | 뉴스 목록 (source, category, limit, offset 필터) |
| GET | `/api/news/{id}` | 뉴스 상세 |
| GET | `/api/stats` | 통계 (카테고리·소스별 건수) |
| POST | `/api/crawl` | 수동 크롤링 트리거 |

API 문서: `http://localhost:8000/docs`

---

## 🎯 수집 대상

| 소스 | URL | 카테고리 |
|------|-----|---------|
| 연합뉴스 | `yna.co.kr/people/personnel` | 인사 |
| 연합뉴스 | `yna.co.kr/people/movement` | 동정 |
| 연합뉴스 | `yna.co.kr/people/obituary-notice` | 부고 |
| 한국경제 | `hankyung.com/people?target[]=인사&period=...` | 인사 |
| 한국경제 | `hankyung.com/people?target[]=부고&period=...` | 부고 |

> 한국경제는 `period` 파라미터(기본 최근 7일)를 자동 생성하여 요청합니다.

---

## 🔧 중복 제거 로직

- 기사 URL을 MD5 해싱하여 `news_hash` 컬럼에 저장
- `INSERT IGNORE` 쿼리로 동일 URL 재수집 시 무시
- 텔레그램 전송 여부(`sent_telegram`)를 별도 관리하여 미전송분만 재전송
