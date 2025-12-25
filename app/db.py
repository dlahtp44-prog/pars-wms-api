import sqlite3

DB_PATH = "WMS.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# ---------- 조회 ----------
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory ORDER BY location, item_code")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_location_items(location):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT item_code, item_name, lot_no, spec, qty
        FROM inventory
        WHERE location=?
        ORDER BY item_code
    """, (location,))
    rows = cur.fetchall()
    conn.close()
    return rows
