# app/db.py
# =====================================
# PARS WMS DB - 최종 안정본
# =====================================

import sqlite3
from datetime import datetime

DB_PATH = "wms.db"


# -------------------------------------
# DB Connection
# -------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH)


# -------------------------------------
# INIT
# -------------------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_code TEXT,
        item_name TEXT,
        brand TEXT,
        spec TEXT,
        location_code TEXT,
        lot TEXT,
        quantity INTEGER,
        PRIMARY KEY (item_code, location_code, lot)
    )
    """)

    # history
    cur.execute("""
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

    conn.commit()
    conn.close()


# -------------------------------------
# INVENTORY
# -------------------------------------
def add_inventory(
    item_code,
    item_name,
    brand,
    spec,
    location_code,
    lot,
    quantity
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT quantity FROM inventory
    WHERE item_code=? AND location_code=? AND lot=?
    """, (item_code, location_code, lot))

    row = cur.fetchone()

    if row:
        cur.execute("""
        UPDATE inventory
        SET quantity = quantity + ?
        WHERE item_code=? AND location_code=? AND lot=?
        """, (quantity, item_code, location_code, lot))
    else:
        cur.execute("""
        INSERT INTO inventory
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item_code, item_name, brand, spec,
            location_code, lot, quantity
        ))

    conn.commit()
    conn.close()


def subtract_inventory(item_code, location_code, lot, quantity):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT quantity FROM inventory
    WHERE item_code=? AND location_code=? AND lot=?
    """, (item_code, location_code, lot))

    row = cur.fetchone()
    if not row:
        raise ValueError("재고가 존재하지 않습니다.")

    if row[0] < quantity:
        raise ValueError("출고 수량이 재고보다 많습니다.")

    cur.execute("""
    UPDATE inventory
    SET quantity = quantity - ?
    WHERE item_code=? AND location_code=? AND lot=?
    """, (quantity, item_code, location_code, lot))

    conn.commit()
    conn.close()


def move_inventory(item_code, from_loc, to_loc, lot, quantity):
    subtract_inventory(item_code, from_loc, lot, quantity)
    add_inventory(
        item_code=item_code,
        item_name="",
        brand="",
        spec="",
        location_code=to_loc,
        lot=lot,
        quantity=quantity
    )


def get_inventory():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_code, item_name, brand, spec,
           location_code, lot, quantity
    FROM inventory
    ORDER BY item_code, location_code
    """)

    rows = cur.fetchall()
    conn.close()

    return rows


# -------------------------------------
# HISTORY
# -------------------------------------
def add_history(action, item_code, loc_from, loc_to, lot, quantity):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO history
    (action, ite
