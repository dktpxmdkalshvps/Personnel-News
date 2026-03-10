"""
MariaDB 연동 모듈 — 인사/부고 뉴스 저장 및 중복 제거
"""
import logging
import os
from datetime import datetime
from typing import Optional

import pymysql
from pymysql.cursors import DictCursor

logger = logging.getLogger(__name__)

# DDL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS news_items (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    news_hash     CHAR(32)     NOT NULL UNIQUE COMMENT 'URL MD5 해시 — 중복 방지 키',
    article_id    VARCHAR(100) NULL,
    source        VARCHAR(20)  NOT NULL COMMENT 'yna | hankyung',
    category      VARCHAR(20)  NOT NULL COMMENT '인사 | 동정 | 부고',
    title         VARCHAR(500) NOT NULL,
    content       MEDIUMTEXT   NOT NULL,
    url           VARCHAR(1000) NOT NULL,
    published_at  DATETIME     NULL,
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    sent_telegram TINYINT(1)   DEFAULT 0 COMMENT '텔레그램 전송 여부',
    INDEX idx_source    (source),
    INDEX idx_category  (category),
    INDEX idx_published (published_at),
    INDEX idx_sent      (sent_telegram)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""


def get_connection() -> pymysql.connections.Connection:
    """환경변수에서 DB 연결 정보 읽기"""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "newsbot"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "personnel_news"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def init_db() -> None:
    """테이블 초기화"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    logger.info("DB 초기화 완료")


def upsert_news(item_dict: dict) -> bool:
    """
    뉴스 저장. news_hash 중복 시 무시.
    Returns True if new record was inserted.
    """
    sql = """
        INSERT IGNORE INTO news_items
            (news_hash, article_id, source, category, title, content, url, published_at)
        VALUES
            (%(news_hash)s, %(article_id)s, %(source)s, %(category)s,
             %(title)s, %(content)s, %(url)s, %(published_at)s)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, item_dict)
            inserted = cur.rowcount > 0
        conn.commit()
    return inserted


def get_unsent_items(limit: int = 50) -> list[dict]:
    """텔레그램 미전송 기사 목록"""
    sql = """
        SELECT * FROM news_items
        WHERE sent_telegram = 0
        ORDER BY published_at DESC, created_at DESC
        LIMIT %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            return cur.fetchall()


def mark_as_sent(news_ids: list[int]) -> None:
    """텔레그램 전송 완료 표시"""
    if not news_ids:
        return
    placeholders = ",".join(["%s"] * len(news_ids))
    sql = f"UPDATE news_items SET sent_telegram = 1 WHERE id IN ({placeholders})"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, news_ids)
        conn.commit()


def get_recent_news(
    source: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """REST API용 최신 뉴스 조회"""
    conditions = []
    params = []

    if source:
        conditions.append("source = %s")
        params.append(source)
    if category:
        conditions.append("category = %s")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"""
        SELECT id, news_hash, source, category, title, url, published_at, created_at
        FROM news_items
        {where}
        ORDER BY published_at DESC, created_at DESC
        LIMIT %s OFFSET %s
    """
    params += [limit, offset]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def get_news_detail(news_id: int) -> Optional[dict]:
    """기사 상세 조회"""
    sql = "SELECT * FROM news_items WHERE id = %s"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (news_id,))
            return cur.fetchone()


def count_news(source: Optional[str] = None, category: Optional[str] = None) -> int:
    """뉴스 총 건수"""
    conditions = []
    params = []
    if source:
        conditions.append("source = %s")
        params.append(source)
    if category:
        conditions.append("category = %s")
        params.append(category)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT COUNT(*) as cnt FROM news_items {where}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return row["cnt"] if row else 0
