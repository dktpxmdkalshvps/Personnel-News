"""
텔레그램 봇 — 인사/동정/부고 뉴스 전송
python-telegram-bot 20.x 사용
"""
import asyncio
import logging
import os

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


class NewsBot:
    def __init__(self, token: str = TELEGRAM_TOKEN, chat_id: str = TELEGRAM_CHAT_ID):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID 환경변수가 설정되지 않았습니다.")
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def send_message_async(self, text: str) -> bool:
        """비동기 메시지 전송"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False,
            )
            return True
        except TelegramError as e:
            logger.error(f"텔레그램 전송 실패: {e}")
            return False

    def send_message(self, text: str) -> bool:
        """동기 래퍼"""
        return asyncio.run(self.send_message_async(text))

    async def send_news_batch_async(self, items: list[dict], delay: float = 0.5) -> list[int]:
        """
        여러 기사 일괄 전송.
        Returns list of successfully sent item IDs.
        """
        sent_ids = []
        for item in items:
            msg = self._format_message(item)
            success = await self.send_message_async(msg)
            if success:
                sent_ids.append(item["id"])
            await asyncio.sleep(delay)  # Rate limit 방지
        return sent_ids

    def send_news_batch(self, items: list[dict]) -> list[int]:
        return asyncio.run(self.send_news_batch_async(items))

    @staticmethod
    def _format_message(item: dict) -> str:
        """DB dict → 텔레그램 메시지 포맷"""
        source_emoji = {"yna": "📰", "hankyung": "📈"}.get(item.get("source", ""), "📋")
        source_name = {"yna": "연합뉴스", "hankyung": "한국경제"}.get(item.get("source", ""), "")
        cat_emoji = {"인사": "🏢", "동정": "🤝", "부고": "🕯️"}.get(item.get("category", ""), "📋")

        date_str = ""
        if item.get("published_at"):
            dt = item["published_at"]
            if hasattr(dt, "strftime"):
                date_str = dt.strftime("%Y.%m.%d %H:%M")
            else:
                date_str = str(dt)[:16].replace("T", " ")

        content = (item.get("content") or "").strip()
        if len(content) > 800:
            content = content[:800] + "…"

        lines = [
            f"{cat_emoji} *{item.get('category', '')}*  {source_emoji} {source_name}",
            "━━━━━━━━━━━━━━━━━━",
            f"*{item.get('title', '')}*",
            "",
            content,
        ]
        if date_str:
            lines.append(f"\n🕐 {date_str}")
        lines.append(f"🔗 [원문 보기]({item.get('url', '')})")

        return "\n".join(lines)

    async def send_summary_async(self, stats: dict) -> None:
        """수집 통계 요약 메시지 전송"""
        msg = (
            "📊 *뉴스 수집 완료*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🏢 인사: {stats.get('인사', 0)}건\n"
            f"🤝 동정: {stats.get('동정', 0)}건\n"
            f"🕯️ 부고: {stats.get('부고', 0)}건\n"
            f"✅ 신규: {stats.get('new', 0)}건  |  🔁 중복: {stats.get('dup', 0)}건"
        )
        await self.send_message_async(msg)

    def send_summary(self, stats: dict) -> None:
        asyncio.run(self.send_summary_async(stats))
