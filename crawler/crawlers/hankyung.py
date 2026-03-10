"""
한국경제 인사/부고 크롤러
- 인사: https://www.hankyung.com/people?target[]=인사&period=YYYY.MM.DD+-+YYYY.MM.DD&keyword=
- 부고: https://www.hankyung.com/people?target[]=부고&period=YYYY.MM.DD+-+YYYY.MM.DD&keyword=

스크린샷 확인 구조:
  - 목록: 기사 링크 목록
  - 상세: h1.headline / div#articletxt.article-body
         <br> 태그로 구분된 인사 목록 (▶ ◇ ▲ ◆ 기호 포함)
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlencode, quote

import requests
from bs4 import BeautifulSoup

from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


def _period_param(days_back: int = 7) -> str:
    """오늘 기준 days_back일 전 ~ 오늘 날짜 문자열 반환 (YYYY.MM.DD+-+YYYY.MM.DD)"""
    today = datetime.now()
    start = today - timedelta(days=days_back)
    return f"{start.strftime('%Y.%m.%d')}+-+{today.strftime('%Y.%m.%d')}"


# 카테고리별 target 파라미터 (URL 인코딩 전)
HANKYUNG_CATEGORIES = {
    "인사": "인사",
    "부고": "부고",
}


class HankyungCrawler(BaseCrawler):
    SOURCE_NAME = "한국경제"
    BASE_URL = "https://www.hankyung.com"
    LIST_BASE = "https://www.hankyung.com/people"

    def _list_url(self, target: str, days_back: int = 7) -> str:
        """카테고리별 목록 URL 생성"""
        period = _period_param(days_back)
        # target[]= 파라미터는 한글 인코딩 필요
        encoded_target = quote(target)
        return (
            f"{self.LIST_BASE}"
            f"?target%5B%5D={encoded_target}"
            f"&period={period}"
            f"&keyword="
        )

    def fetch_list(self) -> list[NewsItem]:
        items = []
        for category, target in HANKYUNG_CATEGORIES.items():
            url = self._list_url(target)
            logger.info(f"[한국경제] {category} 목록 수집: {url}")
            try:
                page_items = self._fetch_category_list(url, category)
                items.extend(page_items)
                time.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"[한국경제] {category} 수집 오류: {e}")
        return items

    def _fetch_category_list(self, url: str, category: str) -> list[NewsItem]:
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        seen_urls: set[str] = set()
        items: list[NewsItem] = []

        # 한국경제 people 목록 페이지 셀렉터 (여러 패턴 시도)
        selectors = [
            "ul.news-list li a",
            "ul.list li a.news-tit",
            "div.list-wrap li a",
            "article a.news-tit",
            ".content-list li a",
        ]
        anchors = []
        for sel in selectors:
            anchors = soup.select(sel)
            if anchors:
                logger.debug(f"[한국경제] 셀렉터 '{sel}' → {len(anchors)}개")
                break

        # fallback: /article/ 패턴 링크
        if not anchors:
            anchors = [
                a for a in soup.find_all("a", href=True)
                if "/article/" in a.get("href", "")
            ]

        for anchor in anchors:
            href = anchor.get("href", "")
            if not href:
                continue
            full_url = href if href.startswith("http") else urljoin(self.BASE_URL, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            title = anchor.get_text(strip=True)
            if not title:
                continue

            time.sleep(self.request_delay)
            item = self.fetch_article(full_url, category, title)
            if item:
                items.append(item)

        return items

    def fetch_article(
        self, url: str, category: str = "인사", prefetch_title: str = ""
    ) -> Optional[NewsItem]:
        """
        한국경제 기사 상세 파싱
        스크린샷 확인 구조:
          - h1.headline : 제목
          - div#articletxt.article-body : 본문
            (▶ ◇ ▲ ◆ 기호 + <br> 태그로 구분된 인사 목록)
          - div.article-timestamp span : 발행일 "입력 YYYY.MM.DD HH:MM"
        """
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # ── 제목 ──
            title_el = soup.select_one("h1.headline, h1.article-title, h1.tit, h1")
            title = title_el.get_text(strip=True) if title_el else prefetch_title

            # ── 본문 (스크린샷 기준: div#articletxt.article-body) ──
            body_el = soup.select_one(
                "div#articletxt.article-body, "
                "div.article-body, "
                "div[id='articletxt']"
            )
            if not body_el:
                body_el = soup.select_one("div[class*='article-body']")

            content = ""
            if body_el:
                for tag in body_el.select("script, style, .ad-wrap, figure, .reporter-info"):
                    tag.decompose()
                # <br> → 줄바꿈
                for br in body_el.find_all("br"):
                    br.replace_with("\n")
                raw = body_el.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in raw.splitlines() if l.strip()]
                content = "\n".join(lines)

            # ── 발행일 (스크린샷: "입력 2026.03.10 17:44") ──
            published_at = None
            date_el = soup.select_one(
                "div.article-timestamp span, "
                "span.txt-date, "
                "time[datetime]"
            )
            if date_el:
                dt_raw = (date_el.get("datetime") or date_el.get_text(strip=True))
                dt_raw = dt_raw.replace("입력", "").replace("수정", "").strip()
                for fmt in (
                    "%Y.%m.%d %H:%M",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                ):
                    try:
                        published_at = datetime.strptime(dt_raw[:16], fmt[:len(dt_raw[:16])])
                        break
                    except ValueError:
                        continue

            article_id = url.rstrip("/").split("/")[-1]

            return NewsItem(
                title=title,
                content=content,
                url=url,
                source="hankyung",
                category=category,
                published_at=published_at,
                article_id=article_id,
            )

        except Exception as e:
            logger.error(f"[한국경제] 기사 수집 오류 ({url}): {e}")
            return None
