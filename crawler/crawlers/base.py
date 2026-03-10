"""
Base crawler class for personnel/obituary news
"""
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """뉴스 아이템 데이터 클래스"""
    title: str
    content: str
    url: str
    source: str  # 'yna' or 'hankyung'
    category: str  # '인사', '동정', '부고'
    published_at: Optional[datetime] = None
    article_id: Optional[str] = None
    news_hash: str = field(init=False)

    def __post_init__(self):
        # URL 기반 고유 해시 생성 (중복 방지)
        self.news_hash = hashlib.md5(self.url.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "article_id": self.article_id,
            "news_hash": self.news_hash,
        }

    def to_telegram_message(self) -> str:
        """텔레그램 전송용 메시지 포맷"""
        source_name = "연합뉴스" if self.source == "yna" else "한국경제"
        date_str = self.published_at.strftime("%Y.%m.%d %H:%M") if self.published_at else ""
        
        lines = [
            f"📋 *{self.category}*  |  {source_name}",
            f"━━━━━━━━━━━━━━━━━━",
            f"*{self.title}*",
            "",
        ]

        # 내용 최대 1000자 제한
        content = self.content.strip()
        if len(content) > 1000:
            content = content[:1000] + "..."
        lines.append(content)

        if date_str:
            lines.append(f"\n🕐 {date_str}")
        lines.append(f"🔗 [원문 보기]({self.url})")

        return "\n".join(lines)


class BaseCrawler(ABC):
    """크롤러 베이스 클래스"""
    
    SOURCE_NAME: str = ""
    BASE_URL: str = ""

    def __init__(self, request_delay: float = 1.5):
        self.request_delay = request_delay
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    @abstractmethod
    def fetch_list(self) -> list[NewsItem]:
        """뉴스 목록 페이지에서 기사 리스트 수집"""
        pass

    @abstractmethod
    def fetch_article(self, url: str) -> Optional[NewsItem]:
        """개별 기사 상세 내용 수집"""
        pass

    def run(self) -> list[NewsItem]:
        """크롤링 실행 진입점"""
        logger.info(f"[{self.SOURCE_NAME}] 크롤링 시작")
        items = self.fetch_list()
        logger.info(f"[{self.SOURCE_NAME}] {len(items)}건 수집 완료")
        return items
