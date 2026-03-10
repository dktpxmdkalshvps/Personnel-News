"""
스케줄러 — APScheduler를 사용한 주기적 크롤링
기본: 매 1시간마다 실행
"""
import logging
import os
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from crawler.main import run_crawl_and_send

# 크롤링 주기 (환경변수로 조정 가능)
# CRON_HOUR: "*/1" = 매 1시간, "9,12,15,18" = 특정 시간대만
CRON_HOUR = os.getenv("CRON_HOUR", "*/1")
CRON_MINUTE = os.getenv("CRON_MINUTE", "0")


def job():
    logger.info("=== 스케줄 크롤링 시작 ===")
    try:
        run_crawl_and_send(use_db=True, send_telegram=True)
    except Exception as e:
        logger.error(f"크롤링 오류: {e}", exc_info=True)
    logger.info("=== 스케줄 크롤링 종료 ===")


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        job,
        trigger=CronTrigger(hour=CRON_HOUR, minute=CRON_MINUTE),
        id="news_crawl",
        max_instances=1,
        misfire_grace_time=300,
    )

    logger.info(f"스케줄러 시작 — 주기: {CRON_HOUR}시 {CRON_MINUTE}분")
    # 시작 시 즉시 한 번 실행
    job()
    scheduler.start()
