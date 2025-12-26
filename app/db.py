# app/db.py
# =========================================
# PARS WMS - DB FINAL (Single Source of Truth)
# =========================================

import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "wms.db"

# -------------------------------------------------
# DB Connection
# -------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# -------------------------------------------------
# INIT
# -------------------------------------------------
def init_db():
    with get_db() as conn:
        c = conn.cursor()

        # INVENTORY
        c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_code TEXT,
            item_name TEXT,
            brand TEXT,
            spec TEXT,
            location TEXT,
            lot TEXT,
            quantity INTEGER
        )
        """)

        # HISTORY
        c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            item_code TEXT,
            location_from TEXT,
            location_to TEXT,
            lot TEXT,
            quantity INTEGER,
            created_at TEXT
        )
        """)

# -------------------------------------------------
# INVENTORY
# -------------------------------------------------
def add_inventory(
    item_code,
    item_name,
    brand,
    spec,
    location,
    lot,
    quantity
):
    with get_db() as conn:
        c = conn.cursor()

        c.execute("""
        SELECT id, quantity FROM inventory
        WHERE item_code=? AND location=? AND lot=?
        """, (item_code, location, lot))

        row = c.fetchone()

        if row:
            c.execute("""
            UPDATE inventory
            SET quantity = quantity + ?
            WHERE id=?
            """, (quantity, row["id"]))
        else:
            c.execute("""
            INSERT INTO inventory
            (item_code, item_name, brand, spec, location, lot, quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item_code, item_name, brand,
                spec, location, lot, quantity
            ))

# -------------------------------------------------
# SUBTRACT (OUTBOUND / MOVE)
# -------------------------------------------------
def subtract_inventory(item_code, location, lot, quantity):
    with get_db() as conn:
        c = conn.cursor()

        c.execute("""
        SELECT id, quantity FROM inventory
        WHERE item_code=? AND location=? AND lot=?
        """, (item_code, location, lot))

        row = c.fetchone()

        if not row:
            raise ValueError("재고가 존재하지 않습니다.")

        if row["quantity"] < quantity:
            raise ValueError("출고 수량이 재고보다 많습니다.")

        new_qty = row["quantity"] - quantity

        if new_qty == 0:
            c.execute("DELETE FROM inventory WHERE id=?", (row["id"],))
        else:
            c.execute("""
            UPDATE inventory
            SET quantity=?
            WHERE id=?
            """, (new_qty, row["id"]))

# -------------------------------------------------
# HISTORY
# -------------------------------------------------
def add_history(
    action,
    item_code,
    location_from,
    location_to,
    lot,
    quantity
):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO history
        (action, item_code, location_from, location_to, lot, quantity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            action,
            item_code,
            location_from,
            location_to,
            lot,
            quantity,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
