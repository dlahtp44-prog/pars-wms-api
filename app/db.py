# app/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "WMS.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # QR 오류 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS qr_errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        qr_raw TEXT,
        err_type TEXT,
        err_msg TEXT,
        is_checked INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ---------- QR 오류 ----------
def log_qr_error(qr_raw, err_type, err_msg):
    conn = get_conn()
    conn.execute("""
        INSERT INTO qr_errors (qr_raw, err_type, err_msg)
        VALUES (?, ?, ?)
    """, (qr_raw, err_type, err_msg))
    conn.commit()
    conn.close()


def get_unchecked_qr_error_count():
    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*) AS cnt FROM qr_errors WHERE is_checked = 0
    """).fetchone()
    conn.close()
    return row["cnt"]


def get_qr_errors(limit=100):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM qr_errors
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows


def mark_qr_errors_checked():
    conn = get_conn()
    conn.execute("UPDATE qr_errors SET is_checked = 1")
    conn.commit()
    conn.close()


# ---------- 차단 로직 ----------
def is_blocked_action(action: str) -> bool:
    """
    치명 오류 3회 이상이면 출고/이동 차단
    """
    conn = get_conn()
    row = conn.execute("""
        SELECT COUNT(*) AS cnt
        FROM qr_errors
        WHERE err_type = 'CRITICAL'
          AND is_checked = 0
    """).fetchone()
    conn.close()

    return row["cnt"] >= 3 and action in ("OUT", "MOVE")
