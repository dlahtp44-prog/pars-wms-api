import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "WMS.db"

# =========================
# DB 연결
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# DB 초기화
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 재고 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER DEFAULT 0,
        UNIQUE(item_code, location)
    )
    """)

    # 작업 이력 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        item_code TEXT,
        qty INTEGER,
        location TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# 작업 이력 기록
# =========================
def log_history(tx_type: str, item_code: str, qty: int, location: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history (tx_type, item_code, qty, location, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        tx_type,
        item_code,
        qty,
        location,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

# =========================
# 작업 이력 조회 (🔥 모든 에러의 핵심)
# =========================
def get_history(limit: int = 100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
