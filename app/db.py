import sqlite3

DB_PATH = "wms.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 재고 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_code TEXT,
        location TEXT,
        qty INTEGER,
        PRIMARY KEY (item_code, location)
    )
    """)

    # 작업 이력 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        item_code TEXT,
        from_loc TEXT,
        to_loc TEXT,
        qty INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

