"""
메인 실행 파일 — 크롤링 → DB 저장 → 텔레그램 전송
"""
import logging
import os
import sys
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("crawler.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

from crawlers import YNACrawler, HankyungCrawler
from db.models import init_db, upsert_news, get_unsent_items, mark_as_sent
from bot.telegram_bot import NewsBot


def run_crawl_and_send(use_db: bool = True, send_telegram: bool = True):
    """
    크롤링 → DB 저장 → 텔레그램 전송 파이프라인
    """
    # 1단계: DB 초기화 (테이블이 없으면 생성)
    if use_db:
        try:
            init_db()
        except Exception as e:
            logger.error(f"DB 초기화 실패: {e}")
            logger.warning("DB 없이 텔레그램 직접 전송 모드로 전환합니다.")
            use_db = False

    # 2단계: 크롤링
    all_items = []
    for CrawlerClass in [YNACrawler, HankyungCrawler]:
        try:
            crawler = CrawlerClass()
            items = crawler.run()
            all_items.extend(items)
        except Exception as e:
            logger.error(f"{CrawlerClass.__name__} 실행 오류: {e}")

    logger.info(f"총 {len(all_items)}건 수집")

    stats = defaultdict(int)
    new_items = []

    # 3단계: DB 저장 또는 직접 처리
    if use_db:
        for item in all_items:
            stats[item.category] += 1
            try:
                is_new = upsert_news(item.to_dict())
                if is_new:
                    stats["new"] += 1
                else:
                    stats["dup"] += 1
            except Exception as e:
                logger.error(f"DB 저장 오류: {e}")
    else:
        # DB 없는 MVP 모드 — 모든 항목을 신규로 처리
        new_items = all_items
        for item in all_items:
            stats[item.category] += 1
        stats["new"] = len(all_items)

    # 4단계: 텔레그램 전송
    if send_telegram:
        try:
            bot = NewsBot()
        except ValueError as e:
            logger.error(f"텔레그램 봇 초기화 실패: {e}")
            return

        if use_db:
            # DB에서 미전송 목록 가져와 전송
            unsent = get_unsent_items(limit=50)
            if unsent:
                logger.info(f"텔레그램 전송 대기: {len(unsent)}건")
                sent_ids = bot.send_news_batch(unsent)
                mark_as_sent(sent_ids)
                logger.info(f"텔레그램 전송 완료: {len(sent_ids)}건")
            bot.send_summary(dict(stats))
        else:
            # MVP 직접 전송
            for item in new_items:
                bot.send_message(item.to_telegram_message())

    logger.info(f"완료 — 인사:{stats['인사']} 동정:{stats['동정']} 부고:{stats['부고']} "
                f"신규:{stats['new']} 중복:{stats['dup']}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="인사/부고 뉴스 크롤러")
    parser.add_argument("--no-db", action="store_true", help="DB 저장 없이 텔레그램 직접 전송 (MVP 모드)")
    parser.add_argument("--no-telegram", action="store_true", help="텔레그램 전송 없이 크롤링만")
    args = parser.parse_args()

    run_crawl_and_send(
        use_db=not args.no_db,
        send_telegram=not args.no_telegram,
    )
