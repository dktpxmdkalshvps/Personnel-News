"""
연합뉴스 인사/동정/부고 크롤러
- 인사:  https://www.yna.co.kr/people/personnel
- 동정:  https://www.yna.co.kr/people/movement
- 부고:  https://www.yna.co.kr/people/obituary-notice
"""
import logging
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .base import BaseCrawler, NewsItem

logger = logging.getLogger(__name__)


class YNACrawler(BaseCrawler):
    SOURCE_NAME = "연합뉴스"
    BASE_URL = "https://www.yna.co.kr"
    PEOPLE_URL = "https://www.yna.co.kr/people/personnel"

    CATEGORY_URLS = {
        "인사": "https://www.yna.co.kr/people/personnel",
        "동정": "https://www.yna.co.kr/people/movement",
        "부고": "https://www.yna.co.kr/people/obituary-notice",
    }

    def fetch_list(self) -> list[NewsItem]:
        items = []
        for category, url in self.CATEGORY_URLS.items():
            try:
                logger.info(f"[연합뉴스] {category} 목록 수집: {url}")
                page_items = self._fetch_category_list(url, category)
                items.extend(page_items)
                time.sleep(self.request_delay)
            except Exception as e:
                logger.error(f"[연합뉴스] {category} 수집 오류: {e}")
        return items

    def _fetch_category_list(self, url: str, category: str) -> list[NewsItem]:
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        items = []
        seen_urls = set()

        # 연합뉴스 목록 페이지 셀렉터 순서대로 시도
        selectors = [
            "div.list-type038 li a.tit-wrap",
            "ul.list li a.tit-wrap",
            "div.alist-w article a",
            "div.item-box01 a.tit-wrap",
            ".news-list li a",
        ]
        anchors = []
        for sel in selectors:
            anchors = soup.select(sel)
            if anchors:
                logger.debug(f"[연합뉴스] 셀렉터 '{sel}' 로 {len(anchors)}개 감지")
                break

        # fallback: 기사 URL 패턴(/view/ 포함) 링크 전체 추출
        if not anchors:
            anchors = [
                a for a in soup.find_all("a", href=True)
                if "/view/" in a["href"] or "/article/" in a["href"]
            ]

        for anchor in anchors:
            href = anchor.get("href", "")
            if not href:
                continue
            full_url = href if href.startswith("http") else urljoin(self.BASE_URL, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            title_el = anchor.select_one("strong.tit, .title, strong")
            title = title_el.get_text(strip=True) if title_el else anchor.get_text(strip=True)
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
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # ── 제목 ──
            title_el = soup.select_one(
                "h1.tit, h1.article-tit, .article-header h1, h2.title, h1"
            )
            title = title_el.get_text(strip=True) if title_el else prefetch_title

            # ── 본문 ──
            body_el = soup.select_one(
                "div.story-news article, "
                "div#articleWrap, "
                "div.article-txt, "
                "div[class*='story-news']"
            )
            content = ""
            if body_el:
                for tag in body_el.select("script, style, .ad-wrap, .promotion, figure"):
                    tag.decompose()
                for br in body_el.find_all("br"):
                    br.replace_with("\n")
                raw = body_el.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in raw.splitlines() if l.strip()]
                content = "\n".join(lines)

            # ── 발행일 ──
            published_at = None
            date_el = soup.select_one(
                "time.update-time, p.update-time, span.txt-date, time[datetime]"
            )
            if date_el:
                dt_raw = (date_el.get("datetime") or date_el.get_text(strip=True)).strip()
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S",
                    "%Y.%m.%d %H:%M",      "%Y-%m-%d %H:%M:%S",
                ):
                    try:
                        published_at = datetime.strptime(dt_raw[:19], fmt[:len(dt_raw[:19])])
                        break
                    except ValueError:
                        continue

            article_id = url.rstrip("/").split("/")[-1]

            return NewsItem(
                title=title,
                content=content,
                url=url,
                source="yna",
                category=category,
                published_at=published_at,
                article_id=article_id,
            )
        except Exception as e:
            logger.error(f"[연합뉴스] 기사 수집 오류 ({url}): {e}")
            return None
