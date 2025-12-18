import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "wms.db")

# =========================
# DB Connection
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
        qty INTEGER DEFAULT 0
    )
    """)

    # 작업 이력 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        location_name TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# 작업 이력 기록 (🔥 핵심)
# =========================
def log_history(
    action,
    location_name,
    brand,
    item_code,
    item_name,
    lot_no,
    spec,
    location,
    qty
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO history (
        action, location_name, brand,
        item_code, item_name, lot_no,
        spec, location, qty, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        action,
        location_name,
        brand,
        item_code,
        item_name,
        lot_no,
        spec,
        location,
        qty,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
