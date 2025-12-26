# app/db.py
# =========================================
# PARS WMS - A안 기준 단일 DB 완성본
# 전체 교체용 (copy & paste 전용)
# 기준점: 이 파일이 "유일한 정답"
# =========================================

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "WMS.db"


# ==================================================
# DB CONNECTION
# ==================================================
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==================================================
# INIT DB
# ==================================================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------
    # ITEMS (제품 마스터)
    # -----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_code TEXT PRIMARY KEY,
        item_name TEXT,
        brand TEXT,
        spec TEXT
    )
    """)

    # -----------------------------
    # LOCATIONS
    # -----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        location_code TEXT PRIMARY KEY,
        warehouse TEXT
    )
    """)

    # -----------------------------
    # INVENTORY
    # -----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_code TEXT,
        location_code TEXT,
        lot TEXT,
        quantity INTEGER,
        PRIMARY KEY (item_code, location_code, lot)
    )
    """)

    # -----------------------------
    # HISTORY
    # -----------------------------
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

    # -----------------------------
    # ADMIN
    # -----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    # 기본 관리자 계정
    cur.execute("""
    INSERT OR IGNORE INTO admin (username, password)
    VALUES ('admin', 'admin123')
    """)

    conn.commit()
    conn.close()


# ==================================================
# INVENTORY CORE FUNCTIONS (A안 기준)
# ==================================================
def get_inventory() -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.item_code, it.item_name, it.brand, it.spec,
               i.location_code, i.lot, i.quantity
        FROM inventory i
        LEFT JOIN items it ON i.item_code = it.item_code
        ORDER BY i.location_code
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_location_items(location_code: str) -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.item_code, it.item_name, it.brand, it.spec,
               i.lot, i.quantity
        FROM inventory i
        LEFT JOIN items it ON i.item_code = it.item_code
        WHERE i.location_code = ?
    """, (location_code,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_inventory(item_code: str, item_name: str, brand: str,
                  spec: str, location_code: str, lot: str, quantity: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO items (item_code, item_name, brand, spec)
        VALUES (?, ?, ?, ?)
    """, (item_code, item_name, brand, spec))

    cur.execute("""
        INSERT INTO inventory (item_code, location_code, lot, quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(item_code, location_code, lot)
        DO UPDATE SET quantity = quantity + ?
    """, (item_code, location_code, lot, quantity, quantity))

    _add_history("INBOUND", item_code, None, location_code, lot, quantity, cur)

    conn.commit()
    conn.close()


def subtract_inventory(item_code: str, location_code: str, lot: str, quantity: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE inventory
        SET quantity = quantity - ?
        WHERE item_code = ? AND location_code = ? AND lot = ?
    """, (quantity, item_code, location_code, lot))

    _add_history("OUTBOUND", item_code, location_code, None, lot, quantity, cur)

    conn.commit()
    conn.close()


def move_inventory(item_code: str, lot: str,
                   location_from: str, location_to: str, quantity: int):
    conn = get_connection()
    cur = conn.cursor()

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
# HISTORY
# ==================================================
def get_history() -> List[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM history
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _add_history(action: str, item_code: str,
                 location_from: Optional[str],
                 location_to: Optional[str],
                 lot: str, quantity: int, cur):
    cur.execute("""
        INSERT INTO history (
            action, item_code, location_from,
            location_to, lot, quantity, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        action,
        item_code,
        location_from,
        location_to,
        lot,
        quantity,
        datetime.now().isoformat()
    ))


# ==================================================
# DASHBOARD
# ==================================================
def dashboard_summary() -> Dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT SUM(quantity) FROM inventory")
    total_qty = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT action, COUNT(*) as cnt
        FROM history
        GROUP BY action
    """)
    actions = {row["action"]: row["cnt"] for row in cur.fetchall()}

    conn.close()

    return {
        "total_inventory": total_qty,
        "actions": actions
    }


# ==================================================
# ADMIN
# ==================================================
def admin_password_ok(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM admin
        WHERE username = ? AND password = ?
    """, (username, password))
    row = cur.fetchone()
    conn.close()
    return row is not None
