# app/db.py
# ==================================================
# PARS WMS - DB Layer (FINAL)
# ==================================================

import sqlite3
from datetime import datetime

DB_PATH = "wms.db"


# ==================================================
# DB Connection
# ==================================================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ==================================================
# INIT DB
# ==================================================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # --------------------------
    # INVENTORY TABLE
    # --------------------------
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

    # --------------------------
    # HISTORY TABLE
    # --------------------------
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


# ==================================================
# INVENTORY - ADD (INBOUND)
# ==================================================
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
        (item_code, item_name, brand, spec, location_code, lot, quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item_code, item_name, brand, spec,
            location_code, lot, quantity
        ))

    # history
    cur.execute("""
    INSERT INTO history
    (action, item_code, location_from, location_to, lot, quantity, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "INBOUND",
        item_code,
        None,
        location_code,
        lot,
        quantity,
        datetime.now().isoformat(sep=" ", timespec="seconds")
    ))

    conn.commit()
    conn.close()


# ==================================================
# INVENTORY - SUBTRACT (OUTBOUND)
# ==================================================
def subtract_inventory(
    item_code,
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

    if not row:
        conn.close()
        raise ValueError("재고가 존재하지 않습니다.")

    if row[0] < quantity:
        conn.close()
        raise ValueError("출고 수량이 재고보다 많습니다.")

    cur.execute("""
    UPDATE inventory
    SET quantity = quantity - ?
    WHERE item_code=? AND location_code=? AND lot=?
    """, (quantity, item_code, location_code, lot))

    # history
    cur.execute("""
    INSERT INTO history
    (action, item_code, location_from, location_to, lot, quantity, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "OUTBOUND",
        item_code,
        location_code,
        None,
        lot,
        quantity,
        datetime.now().isoformat(sep=" ", timespec="seconds")
    ))

    conn.commit()
    conn.close()


# ==================================================
# INVENTORY - MOVE
# ==================================================
def move_inventory(
    item_code,
    from_location,
    to_location,
    lot,
    quantity
):
    conn = get_conn()
    cur = conn.cursor()

    # source check
    cur.execute("""
    SELECT quantity FROM inventory
    WHERE item_code=? AND location_code=? AND lot=?
    """, (item_code, from_location, lot))

    row = cur.fetchone()

    if not row:
        conn.close()
        raise ValueError("출발지 재고가 없습니다.")

    if row[0] < quantity:
        conn.close()
        raise ValueError("이동 수량이 재고보다 많습니다.")

    # subtract source
    cur.execute("""
    UPDATE inventory
    SET quantity = quantity - ?
    WHERE item_code=? AND location_code=? AND lot=?
    """, (quantity, item_code, from_location, lot))

    # add destination
    cur.execute("""
    SELECT quantity FROM inventory
    WHERE item_code=? AND location_code=? AND lot=?
    """, (item_code, to_location, lot))

    if cur.fetchone():
        cur.execute("""
        UPDATE inventory
        SET quantity = quantity + ?
        WHERE item_code=? AND location_code=? AND lot=?
        """, (quantity, item_code, to_location, lot))
    else:
        cur.execute("""
        INSERT INTO inventory
        (item_code, item_name, brand, spec, location_code, lot, quantity)
        SELECT item_code, item_name, brand, spec, ?, lot, ?
        FROM inventory
        WHERE item_code=? AND location_code=? AND lot=?
        """, (to_location, quantity, item_code, from_location, lot))

    # history
    cur.execute("""
    INSERT INTO history
    (action, item_code, location_from, location_to, lot, quantity, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "MOVE",
        item_code,
        from_location,
        to_location,
        lot,
        quantity,
        datetime.now().isoformat(sep=" ", timespec="seconds")
    ))

    conn.commit()
    conn.close()


# ==================================================
# GET INVENTORY
# ==================================================
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_code, item_name, brand, spec,
           location_code, lot, quantity
    FROM inventory
    WHERE quantity > 0
    ORDER BY item_code, location_code
    """)

    rows = cur.fetchall()
    conn.close()

    return rows


# ==================================================
# GET INVENTORY BY LOCATION
# ==================================================
def get_inventory_by_location(location_code):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_code, item_name, brand, spec, lot, quantity
    FROM inventory
    WHERE location_code=? AND quantity > 0
    """, (location_code,))

    rows = cur.fetchall()
    conn.close()
    return rows


# ==================================================
# GET HISTORY
# ==================================================
def get_history():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT action, item_code, location_from,
           location_to, lot, quantity, created_at
    FROM history
    ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows
