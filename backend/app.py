"""
FastAPI 백엔드 — React 대시보드용 REST API
"""
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# 경로 조정 (백엔드 디렉토리에서 실행 시)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "crawler"))

from db.models import (
    init_db,
    get_recent_news,
    get_news_detail,
    count_news,
)

app = FastAPI(
    title="인사/부고 뉴스 API",
    description="연합뉴스·한국경제 인사·동정·부고 뉴스 수집 시스템",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    try:
        init_db()
    except Exception as e:
        print(f"[WARNING] DB 연결 실패: {e}")


# ─────────────────────────────────────────────
#  뉴스 목록 API
# ─────────────────────────────────────────────
@app.get("/api/news")
def list_news(
    source: Optional[str] = Query(None, description="yna | hankyung"),
    category: Optional[str] = Query(None, description="인사 | 동정 | 부고"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    뉴스 목록 조회
    - source: yna(연합뉴스) 또는 hankyung(한국경제), 없으면 전체
    - category: 인사·동정·부고, 없으면 전체
    """
    items = get_recent_news(source=source, category=category, limit=limit, offset=offset)
    total = count_news(source=source, category=category)

    # datetime 직렬화
    for item in items:
        for key in ("published_at", "created_at"):
            if item.get(key) and hasattr(item[key], "isoformat"):
                item[key] = item[key].isoformat()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": items,
    }


# ─────────────────────────────────────────────
#  뉴스 상세 API
# ─────────────────────────────────────────────
@app.get("/api/news/{news_id}")
def get_news(news_id: int):
    item = get_news_detail(news_id)
    if not item:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    for key in ("published_at", "created_at"):
        if item.get(key) and hasattr(item[key], "isoformat"):
            item[key] = item[key].isoformat()
    return item


# ─────────────────────────────────────────────
#  통계 API
# ─────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    """카테고리·소스별 집계"""
    stats = {
        "total": count_news(),
        "by_category": {
            "인사": count_news(category="인사"),
            "동정": count_news(category="동정"),
            "부고": count_news(category="부고"),
        },
        "by_source": {
            "yna": count_news(source="yna"),
            "hankyung": count_news(source="hankyung"),
        },
    }
    return stats


# ─────────────────────────────────────────────
#  수동 크롤링 트리거 API (관리자용)
# ─────────────────────────────────────────────
@app.post("/api/crawl")
def trigger_crawl():
    """수동으로 크롤링 실행"""
    from main import run_crawl_and_send
    try:
        run_crawl_and_send(use_db=True, send_telegram=True)
        return {"status": "ok", "message": "크롤링 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
