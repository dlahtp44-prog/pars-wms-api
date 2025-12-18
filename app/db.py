import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "WMS.db")

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

    # 재고 테이블 (예시)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_code TEXT,
        brand TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER,
        PRIMARY KEY (item_code, location)
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# =========================
# ✅ 작업 이력 기록 (입고/출고/이동 공용)
# =========================
def log_history(tx_type: str, item_code: str, qty: int, location: str):
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO history (tx_type, item_code, qty, location)
        VALUES (?, ?, ?, ?)
        """,
        (tx_type, item_code, qty, location)
    )
    conn.commit()
    conn.close()


# =========================
# ✅ 작업 이력 조회 (Page / API 공용)
# =========================
def get_history():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            tx_type,
            item_code,
            qty,
            location,
            created_at
        FROM history
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return rows
