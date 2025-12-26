# app/db.py
# =========================================
# PARS WMS - A안 기준 DB 최종본
# 전체 교체용 (copy & paste 전용)
# =========================================

import sqlite3
from typing import List, Dict
from datetime import datetime

DB_PATH = "WMS.db"


# ==================================================
# CONNECTION
# ==================================================
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================================================
# INIT DB (개발용)
# ⚠️ 서버 재시작 시 데이터 초기화됨
# ==================================================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # inventory
    cur.execute("DROP TABLE IF EXISTS inventory")
    cur.execute("""
        CREATE TABLE inventory (
            item_code TEXT,
            location_code TEXT,
            lot TEXT,
            quantity INTEGER,
            PRIMARY KEY (item_code, location_code, lot)
        )
    """)

    # history
    cur.execute("DROP TABLE IF EXISTS history")
    cur.execute("""
        CREATE TABLE history (
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
# INTERNAL: HISTORY INSERT
# ==================================================
def _add_history(action, item_code, loc_from, loc_to, lot, qty, cur):
    cur.execute("""
        INSERT INTO history
        (action, item_code, location_from, location_to, lot, quantity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        action,
        item_code,
        loc_from,
        loc_to,
        lot,
        qty,
        datetime.now().isoformat(timespec="seconds")
    ))


# ==================================================
# INBOUND
# ==================================================
def add_inventory(item_code: str, location_code: str, lot: str, quantity: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory (item_code, location_code, lot, quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(item_code, location_code, lot)
        DO UPDATE SET quantity = quantity + ?
    """, (item_code, location_code, lot, quantity, quantity))

    _add_history("INBOUND", item_code, None, location_code, lot, quantity, cur)

    conn.commit()
    conn.close()


# ==================================================
# OUTBOUND
# ==================================================
def subtract_inventory(item_code: str, location_code: str, lot: str, quantity: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT quantity FROM inventory
        WHERE item_code = ? AND location_code = ? AND lot = ?
    """, (item_code, location_code, lot))

    row = cur.fetchone()
    if not row or row["quantity"] < quantity:
        conn.close()
        raise ValueError("출고 수량이 재고보다 많습니다.")

    cur.execute("""
        UPDATE inventory
        SET quantity = quantity - ?
        WHERE item_code = ? AND location_code = ? AND lot = ?
    """, (quantity, item_code, location_code, lot))

    _add_history("OUTBOUND", item_code, location_code, None, lot, quantity, cur)

    conn.commit()
    conn.close()


# ==================================================
# MOVE
# ==================================================
def move_inventory(item_code: str, lot: str,
                   location_from: str, location_to: str, quantity: int):
    conn = get_connection()
    cur = conn.cursor()

    # 출발지 재고 확인
    cur.execute("""
        SELECT quantity FROM inventory
        WHERE item_code = ? AND location_code = ? AND lot = ?
    """, (item_code, location_from, lot))

    row = cur.fetchone()
    if not row or row["quantity"] < quantity:
        conn.close()
        raise ValueError("이동 수량이 재고보다 많습니다.")

    # FROM 차감
    cur.execute("""
        UPDATE inventory
        SET quantity = quantity - ?
        WHERE item_code = ? AND location_code = ? AND lot = ?
    """, (quantity, item_code, location_from, lot))

    # TO 증가
    cur.execute("""
        INSERT INTO inventory (item_code, location_code, lot, quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(item_code, location_code, lot)
        DO UPDATE SET quantity = quantity + ?
    """, (item_code, location_to, lot, quantity, quantity))

    _add_history("MOVE", item_code, location_from, location_to, lot, quantity, cur)

    conn.commit()
    conn.close()


# ==================================================
# INVENTORY QUERY
# ==================================================
def get_inventory(item_code=None, location_code=None, lot=None) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT item_code, location_code, lot, quantity
        FROM inventory
        WHERE 1=1
    """
    params = []

    if item_code:
        sql += " AND item_code = ?"
        params.append(item_code)
    if location_code:
        sql += " AND location_code = ?"
        params.append(location_code)
    if lot:
        sql += " AND lot = ?"
        params.append(lot)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


# ==================================================
# HISTORY / REPORT (단일 기준)
# ==================================================
def get_history(action=None, start_date=None, end_date=None) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT
          action,
          item_code,
          lot,
          location_from,
          location_to,
          quantity,
          created_at
        FROM history
        WHERE 1=1
    """
    params = []

    if action:
        sql += " AND action = ?"
        params.append(action)

    if start_date:
        sql += " AND date(created_at) >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND date(created_at) <= ?"
        params.append(end_date)

    sql += " ORDER BY created_at DESC"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]
