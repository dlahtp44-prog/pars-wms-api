
# app/db.py
import sqlite3

DB_PATH = "wms.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 재고 테이블 (엑셀 1:1 대응)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT,
        brand TEXT,
        item TEXT,
        item_name TEXT,
        lot TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER
    )
    """)

    # 작업 이력
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        item TEXT,
        qty INTEGER,
        remark TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )
    """)

    conn.commit()
    conn.close()



def log_history(type, item, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (type, item, qty, remark, created_at) VALUES (?, ?, ?, ?, ?)",
        (type, item, qty, remark, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
