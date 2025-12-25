# app/db.py
import os
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "WMS.db")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")  # Railway ENV로 꼭 바꾸기 권장


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # inventory: 재고 (업무 핵심)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location TEXT NOT NULL DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL DEFAULT '',
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL DEFAULT '',
        spec TEXT DEFAULT '',
        qty REAL NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now','localtime')),
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

    # history: 이력 (롤백/대시보드/추적)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,                 -- IN / OUT / MOVE
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location TEXT DEFAULT '',              -- IN/OUT 기준 location (MOVE는 from_location)
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL DEFAULT '',
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL DEFAULT '',
        spec TEXT DEFAULT '',
        qty REAL NOT NULL DEFAULT 0,
        remark TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )
    """)

    conn.commit()
    conn.close()


def admin_password_ok(pw: str) -> bool:
    return (pw or "") == ADMIN_PASSWORD


# -------------------------
# 재고 조회
# -------------------------
def get_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    sql = """
    SELECT
        warehouse, location, brand, item_code, item_name, lot_no, spec,
        qty, updated_at
    FROM inventory
    WHERE 1=1
    """
    params: List[Any] = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    if location is not None and location != "":
        sql += " AND location = ?"
        params.append(location)

    if q:
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ?)"
        kw = f"%{q}%"
        params.extend([kw, kw, kw])

    sql += " ORDER BY item_code, lot_no"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_location_items(warehouse: str, location: str) -> List[Dict[str, Any]]:
    return get_inventory(warehouse=warehouse, location=location, q=None)


# -------------------------
# 이력 조회
# -------------------------
def get_history(limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "",
    from_location: str = "",
    to_location: str = "",
    brand: str = ""
) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location,
         brand, item_code, item_name, lot_no, spec, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location, from_location, to_location,
        brand, item_code, item_name, lot_no, spec, float(qty), remark
    ))
    tx_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(tx_id)


# -------------------------
# 재고 증감 (핵심 로직)
# -------------------------
def _upsert_inventory(
    warehouse: str, location: str,
    brand: str,
    item_code: str, item_name: str, lot_no: str, spec: str,
    delta_qty: float
) -> None:
    conn = get_conn()
    cur = conn.cursor()

    # 기존 행 있으면 qty += delta_qty, 없으면 새로 insert
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            brand = excluded.brand,
            item_name = excluded.item_name,
            spec = excluded.spec,
            qty = qty + excluded.qty,
            updated_at = datetime('now','localtime')
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, float(delta_qty)))

    conn.commit()
    conn.close()


def get_current_qty(warehouse: str, location: str, item_code: str, lot_no: str) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    row = cur.fetchone()
    conn.close()
    return float(row["qty"]) if row else 0.0


def add_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "입고"
) -> int:
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty는 0보다 커야 합니다.")

    _upsert_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    return log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=remark,
        brand=brand
    )


def subtract_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "출고",
    block_negative: bool = True
) -> int:
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty는 0보다 커야 합니다.")

    current = get_current_qty(warehouse, location, item_code, lot_no)
    after = current - qty
    if block_negative and after < 0:
        raise ValueError(f"재고 부족(음수 차단): 현재 {current}, 출고 {qty}")

    _upsert_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, -qty)
    return log_history(
        tx_type="OUT",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=remark,
        brand=brand
    )


def move_inventory(
    warehouse: str,
    from_location: str,
    to_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "이동",
    block_negative: bool = True
) -> int:
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty는 0보다 커야 합니다.")
    if not from_location or not to_location:
        raise ValueError("from_location / to_location이 필요합니다.")
    if from_location == to_location:
        raise ValueError("출발/도착 로케이션이 같습니다.")

    # 1) 출발지 차감
    subtract_inventory(
        warehouse=warehouse,
        location=from_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=f"{remark} (from {from_location} -> {to_location})",
        block_negative=block_negative
    )
    # 2) 도착지 증가
    add_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=f"{remark} (to {to_location})"
    )

    # 3) MOVE 이력 1줄로 남김(관리/조회용)
    return log_history(
        tx_type="MOVE",
        warehouse=warehouse,
        location=from_location,
        from_location=from_location,
        to_location=to_location,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=remark,
        brand=brand
    )


# -------------------------
# 롤백(실수 복구)
# -------------------------
def rollback(tx_id: int, block_negative: bool = True) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    tx = cur.fetchone()
    if not tx:
        conn.close()
        raise ValueError("해당 이력이 없습니다.")

    tx = dict(tx)
    conn.close()

    t = tx["tx_type"]
    wh = tx["warehouse"]
    loc = tx.get("location") or ""
    frm = tx.get("from_location") or ""
    to = tx.get("to_location") or ""
    brand = tx.get("brand") or ""
    item_code = tx["item_code"]
    item_name = tx.get("item_name") or ""
    lot_no = tx["lot_no"]
    spec = tx.get("spec") or ""
    qty = float(tx["qty"])

    # 원복은 반대로
    if t == "IN":
        # 입고 취소 = 출고
        subtract_inventory(wh, loc, brand, item_code, item_name, lot_no, spec, qty, remark=f"롤백(IN#{tx_id})", block_negative=block_negative)
    elif t == "OUT":
        # 출고 취소 = 입고
        add_inventory(wh, loc, brand, item_code, item_name, lot_no, spec, qty, remark=f"롤백(OUT#{tx_id})")
    elif t == "MOVE":
        # 이동 취소 = 역이동
        move_inventory(wh, to, frm, brand, item_code, item_name, lot_no, spec, qty, remark=f"롤백(MOVE#{tx_id})", block_negative=block_negative)
    else:
        raise ValueError("알 수 없는 tx_type")

    # 롤백 이력 기록(추적용)
    log_history(
        tx_type="ROLLBACK",
        warehouse=wh,
        location=loc or frm,
        from_location=frm,
        to_location=to,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=f"rollback of #{tx_id}"
    )


# -------------------------
# 대시보드 요약
# -------------------------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS s
        FROM history
        WHERE tx_type='IN'
          AND date(created_at) = date('now','localtime')
    """)
    inbound_today = float(cur.fetchone()["s"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS s
        FROM history
        WHERE tx_type='OUT'
          AND date(created_at) = date('now','localtime')
    """)
    outbound_today = float(cur.fetchone()["s"])

    cur.execute("SELECT IFNULL(SUM(qty),0) AS s FROM inventory")
    total_stock = float(cur.fetchone()["s"])

    cur.execute("SELECT COUNT(*) AS c FROM inventory WHERE qty < 0")
    negative_count = int(cur.fetchone()["c"])

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_count": negative_count
    }
