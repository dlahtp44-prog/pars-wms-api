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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL,
        UNIQUE(warehouse, location, item_code, lot_no)
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def add_inventory(warehouse, location, item, lot, qty):
    conn = get_conn()
    cur = conn.cursor()

    # 🔴 음수 방지
    cur.execute("""
    SELECT IFNULL(SUM(qty),0) FROM inventory
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item, lot))
    current = cur.fetchone()[0]

    if current + qty < 0:
        raise ValueError("재고 부족")

    cur.execute("""
    INSERT INTO inventory VALUES (?,?,?,?,?)
    ON CONFLICT DO UPDATE SET qty = qty + ?
    """, (warehouse, location, item, lot, qty, qty))

    cur.execute("""
    INSERT INTO history (tx_type, warehouse, location, item_code, lot_no, qty)
    VALUES (?,?,?,?,?,?)
    """, ("IN" if qty > 0 else "OUT", warehouse, location, item, lot, qty))

    conn.commit()
    conn.close()

def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    r = cur.fetchone()
    if not r:
        return

    add_inventory(
        r["warehouse"], r["location"],
        r["item_code"], r["lot_no"],
        -r["qty"]
    )

    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
