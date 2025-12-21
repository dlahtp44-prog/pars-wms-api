# app/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "WMS.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        brand TEXT,
        item_code TEXT NOT NULL,
        item_name TEXT,
        lot_no TEXT NOT NULL,
        spec TEXT,
        qty REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # UPSERT을 위한 UNIQUE 인덱스 (핵심)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
    """)

    # history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        remark TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def log_history(
    tx_type: str,
    warehouse: str = "",
    location: str = "",
    item_code: str = "",
    item_name: str = "",
    lot_no: str = "",
    spec: str = "",
    qty: float = 0,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark
    ))
    conn.commit()
    conn.close()


def get_inventory(warehouse: str = "", location: str = "", q: str = ""):
    """
    재고조회:
    - warehouse/location 필터 가능
    - q: 품번(item_code) 또는 lot_no 검색
    """
    conn = get_conn()
    cur = conn.cursor()

    where = []
    params = []

    if warehouse:
        where.append("warehouse = ?")
        params.append(warehouse)

    if location:
        where.append("location = ?")
        params.append(location)

    if q:
        where.append("(item_code LIKE ? OR lot_no LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            SUM(qty) as qty
        FROM inventory
        {where_sql}
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code, lot_no, warehouse, location
    """

    rows = [dict(r) for r in cur.execute(sql, params).fetchall()]
    conn.close()
    return rows


def get_history(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()
    rows = [dict(r) for r in cur.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()]
    conn.close()
    return rows
