# app/db.py
import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = os.getenv("DB_PATH", "WMS.db")


# -------------------------
# DB 연결
# -------------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# DB 초기화
# -------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location  TEXT NOT NULL DEFAULT '',
        brand     TEXT NOT NULL DEFAULT '',
        item_code TEXT NOT NULL DEFAULT '',
        item_name TEXT NOT NULL DEFAULT '',
        lot_no    TEXT NOT NULL DEFAULT '',
        spec      TEXT NOT NULL DEFAULT '',
        qty       REAL NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL DEFAULT (DATETIME('now','localtime')),
        UNIQUE(warehouse, location, item_code, lot_no)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,              -- IN / OUT / MOVE
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location  TEXT NOT NULL DEFAULT '', -- IN/OUT일 때 위치, MOVE일 때 to_location 기본값
        from_location TEXT NOT NULL DEFAULT '',
        to_location   TEXT NOT NULL DEFAULT '',
        brand     TEXT NOT NULL DEFAULT '',
        item_code TEXT NOT NULL DEFAULT '',
        item_name TEXT NOT NULL DEFAULT '',
        lot_no    TEXT NOT NULL DEFAULT '',
        spec      TEXT NOT NULL DEFAULT '',
        qty       REAL NOT NULL DEFAULT 0,
        remark    TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (DATETIME('now','localtime'))
    );
    """)

    conn.commit()
    conn.close()


# -------------------------
# 공통: 재고 upsert
# -------------------------
def _upsert_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    delta_qty: float
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now','localtime'))
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            brand=excluded.brand,
            item_name=excluded.item_name,
            spec=excluded.spec,
            qty = inventory.qty + excluded.qty,
            updated_at=DATETIME('now','localtime')
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, float(delta_qty)))

    conn.commit()
    conn.close()


# -------------------------
# 이력 기록
# -------------------------
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    *,
    from_location: str = "",
    to_location: str = "",
    brand: str = "",
    item_name: str = "",
    spec: str = "",
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location,
         brand, item_code, item_name, lot_no, spec, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now','localtime'))
    """, (
        tx_type, warehouse, location, from_location, to_location,
        brand, item_code, item_name, lot_no, spec, float(qty), remark
    ))

    conn.commit()
    conn.close()


# -------------------------
# 입고
# -------------------------
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
):
    qty = float(qty or 0)
    if qty <= 0:
        raise ValueError("qty must be > 0")

    _upsert_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, +qty)
    log_history(
        "IN", warehouse, location, item_code, lot_no, qty,
        brand=brand, item_name=item_name, spec=spec, remark=remark
    )


# -------------------------
# 출고
# -------------------------
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
):
    qty = float(qty or 0)
    if qty <= 0:
        raise ValueError("qty must be > 0")

    # 현재고 확인
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    row = cur.fetchone()
    current = float(row["qty"]) if row else 0.0
    conn.close()

    if block_negative and (current - qty) < 0:
        raise ValueError(f"재고 부족: 현재 {current}, 출고 {qty}")

    _upsert_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, -qty)
    log_history(
        "OUT", warehouse, location, item_code, lot_no, qty,
        brand=brand, item_name=item_name, spec=spec, remark=remark
    )


# -------------------------
# 이동 (from -> to)
# -------------------------
def move_inventory(
    warehouse: str,
    item_code: str,
    lot_no: str,
    qty: float,
    from_location: str,
    to_location: str,
    *,
    brand: str = "",
    item_name: str = "",
    spec: str = "",
    remark: str = "이동",
    block_negative: bool = True
):
    qty = float(qty or 0)
    if qty <= 0:
        raise ValueError("qty must be > 0")
    if not from_location or not to_location:
        raise ValueError("from_location/to_location required")
    if from_location == to_location:
        raise ValueError("from_location and to_location must be different")

    # from 재고 확인
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, from_location, item_code, lot_no))
    row = cur.fetchone()
    current = float(row["qty"]) if row else 0.0
    conn.close()

    if block_negative and (current - qty) < 0:
        raise ValueError(f"이동 불가(재고 부족): 현재 {current}, 이동 {qty}")

    # subtract from
    _upsert_inventory(warehouse, from_location, brand, item_code, item_name, lot_no, spec, -qty)
    # add to
    _upsert_inventory(warehouse, to_location, brand, item_code, item_name, lot_no, spec, +qty)

    # history: MOVE는 location=to_location로 통일
    log_history(
        "MOVE", warehouse, to_location, item_code, lot_no, qty,
        from_location=from_location, to_location=to_location,
        brand=brand, item_name=item_name, spec=spec, remark=remark
    )


# -------------------------
# 조회: inventory / history
# -------------------------
def get_inventory(q: str = "") -> List[Dict[str, Any]]:
    q = (q or "").strip()
    conn = get_conn()
    cur = conn.cursor()

    if q:
        like = f"%{q}%"
        cur.execute("""
            SELECT * FROM inventory
            WHERE item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR location LIKE ? OR brand LIKE ?
            ORDER BY updated_at DESC
        """, (like, like, like, like, like))
    else:
        cur.execute("SELECT * FROM inventory ORDER BY updated_at DESC")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_history(limit: int = 200, q: str = "") -> List[Dict[str, Any]]:
    q = (q or "").strip()
    conn = get_conn()
    cur = conn.cursor()

    if q:
        like = f"%{q}%"
        cur.execute("""
            SELECT * FROM history
            WHERE item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR location LIKE ? OR from_location LIKE ? OR to_location LIKE ?
            ORDER BY id DESC
            LIMIT ?
        """, (like, like, like, like, like, like, int(limit)))
    else:
        cur.execute("""
            SELECT * FROM history
            ORDER BY id DESC
            LIMIT ?
        """, (int(limit),))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------
# 대시보드 요약 (dict 리턴 고정!)
# -------------------------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='IN' AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = float(cur.fetchone()[0])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='OUT' AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = float(cur.fetchone()[0])

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = float(cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative_count = int(cur.fetchone()[0])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM inventory
        WHERE location IS NULL OR location=''
    """)
    no_location_qty = float(cur.fetchone()[0])

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_count": negative_count,
        "no_location_qty": no_location_qty,
    }


# -------------------------
# 로케이션 목록/로케이션 재고
# -------------------------
def get_locations(warehouse: str = "MAIN") -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT location, IFNULL(SUM(qty),0) AS qty_sum, COUNT(*) AS sku_count
        FROM inventory
        WHERE warehouse=?
        GROUP BY location
        ORDER BY location ASC
    """, (warehouse,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_location_items(warehouse: str, location: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM inventory
        WHERE warehouse=? AND location=?
        ORDER BY item_code ASC, lot_no ASC
    """, (warehouse, location))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------
# 롤백 (관리자)
# -------------------------
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (int(tx_id),))
    tx = cur.fetchone()
    if not tx:
        conn.close()
        raise ValueError("해당 이력 없음")

    tx = dict(tx)
    tx_type = tx["tx_type"]
    wh = tx["warehouse"]
    item_code = tx["item_code"]
    lot_no = tx["lot_no"]
    qty = float(tx["qty"])
    brand = tx.get("brand", "") or ""
    item_name = tx.get("item_name", "") or ""
    spec = tx.get("spec", "") or ""

    # 되돌리기
    if tx_type == "IN":
        # 입고 롤백 = 재고 감소
        _upsert_inventory(wh, tx["location"], brand, item_code, item_name, lot_no, spec, -qty)
    elif tx_type == "OUT":
        # 출고 롤백 = 재고 증가
        _upsert_inventory(wh, tx["location"], brand, item_code, item_name, lot_no, spec, +qty)
    elif tx_type == "MOVE":
        # 이동 롤백 = to에서 빼고 from으로 더함
        _upsert_inventory(wh, tx["to_location"], brand, item_code, item_name, lot_no, spec, -qty)
        _upsert_inventory(wh, tx["from_location"], brand, item_code, item_name, lot_no, spec, +qty)
    else:
        conn.close()
        raise ValueError("지원하지 않는 tx_type")

    # 롤백 이력 추가 (원본 삭제는 안함)
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location,
         brand, item_code, item_name, lot_no, spec, qty, remark, created_at)
        VALUES ('ROLLBACK', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATETIME('now','localtime'))
    """, (
        wh,
        tx.get("location",""),
        tx.get("from_location",""),
        tx.get("to_location",""),
        brand, item_code, item_name, lot_no, spec,
        qty,
        f"rollback of #{tx_id}"
    ))

    conn.commit()
    conn.close()


# -------------------------
# 관리자 비밀번호 체크
# -------------------------
def admin_password_ok(pw: str) -> bool:
    admin_pw = os.getenv("ADMIN_PASSWORD", "1234")
    return (pw or "") == admin_pw
