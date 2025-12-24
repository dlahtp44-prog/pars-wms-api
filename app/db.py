# app/db.py
import os
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from hashlib import sha256
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "WMS.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory: (창고,로케이션,품번,LOT) 단위로 수량 관리
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL,
        spec TEXT DEFAULT '',
        qty REAL DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now','localtime')),
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

    # history: 모든 트랜잭션 기록 + 롤백용
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,          -- IN/OUT/MOVE
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,         -- IN/OUT은 location, MOVE는 from_location 저장
        to_location TEXT DEFAULT '',     -- MOVE 목적지
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL,
        spec TEXT DEFAULT '',
        qty REAL NOT NULL,
        remark TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )
    """)

    # 간단 권한(세션)용 admin 설정
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        k TEXT PRIMARY KEY,
        v TEXT NOT NULL
    )
    """)

    # 기본 관리자 비번(없을 때만)
    admin_pw = os.getenv("ADMIN_PASSWORD", "1234")
    admin_hash = sha256(admin_pw.encode("utf-8")).hexdigest()
    cur.execute("INSERT OR IGNORE INTO settings(k,v) VALUES('admin_pw_hash', ?)", (admin_hash,))

    conn.commit()
    conn.close()

# ---------------------------
# 공용: history 기록
# ---------------------------
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    item_name: str = "",
    spec: str = "",
    to_location: str = "",
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history(tx_type, warehouse, location, to_location, item_code, item_name, lot_no, spec, qty, remark)
        VALUES(?,?,?,?,?,?,?,?,?,?)
    """, (tx_type, warehouse, location, to_location, item_code, item_name, lot_no, spec, float(qty), remark))
    conn.commit()
    conn.close()

# ---------------------------
# 재고 CRUD (핵심)
# ---------------------------
def add_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = "IN"
):
    qty = float(qty)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES(?,?,?,?,?,?,?,?, datetime('now','localtime'))
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
          brand=excluded.brand,
          item_name=excluded.item_name,
          spec=excluded.spec,
          qty = inventory.qty + excluded.qty,
          updated_at=datetime('now','localtime')
    """, (warehouse, location, brand or "", item_code, item_name or "", lot_no, spec or "", qty))
    conn.commit()
    conn.close()

    log_history("IN", warehouse, location, item_code, lot_no, qty, item_name=item_name, spec=spec, remark=remark)

def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "OUT",
    block_negative: bool = True
):
    qty = float(qty)
    conn = get_conn()
    cur = conn.cursor()

    # 현재 재고 조회
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS q
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    current = float(cur.fetchone()["q"])

    if block_negative and current - qty < 0:
        conn.close()
        raise ValueError(f"음수 재고 방지: 현재 {current}, 출고 {qty}")

    # 차감: 없으면 레코드 생성(음수 방지 OFF일 때만 의미)
    cur.execute("""
        INSERT INTO inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES(?,?,?,?,?,?,?, ?, datetime('now','localtime'))
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
          qty = inventory.qty - excluded.qty,
          updated_at=datetime('now','localtime')
    """, (warehouse, location, "", item_code, "", lot_no, "", qty))

    conn.commit()
    conn.close()

    log_history("OUT", warehouse, location, item_code, lot_no, qty, remark=remark)

def move_inventory(
    warehouse: str,
    from_location: str,
    to_location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "MOVE",
    block_negative: bool = True
):
    qty = float(qty)
    # 1) 출고(원 위치 차감)
    subtract_inventory(
        warehouse=warehouse,
        location=from_location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark=f"{remark}: {from_location} -> {to_location}",
        block_negative=block_negative
    )
    # 2) 입고(목적 위치 증가)
    add_inventory(
        warehouse=warehouse,
        location=to_location,
        brand="",
        item_code=item_code,
        item_name="",
        lot_no=lot_no,
        spec="",
        qty=qty,
        remark=f"{remark}: {from_location} -> {to_location}"
    )
    # 3) MOVE 이력 하나로도 남기고 싶으면(선택)
    log_history("MOVE", warehouse, from_location, item_code, lot_no, qty, to_location=to_location, remark=remark)

# ---------------------------
# 조회 (여기 q 파라미터가 핵심!)
# ---------------------------
def get_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    sql = """
    SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at
    FROM inventory
    WHERE 1=1
    """
    params: List[Any] = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)
    if location:
        sql += " AND location = ?"
        params.append(location)
    if q is not None and q != "":
        sql += """ AND (
            item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR location LIKE ?
        )"""
        kw = f"%{q}%"
        params.extend([kw, kw, kw, kw])

    sql += " ORDER BY location, item_code, lot_no"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history(limit: int = 300) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (int(limit),))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def rollback(tx_id: int):
    """
    history 1건을 되돌림:
      - IN  -> 동일 수량 OUT(차감)
      - OUT -> 동일 수량 IN(증가)
      - MOVE -> from/to를 역으로 적용(가능할 때)
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (int(tx_id),))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("기록 없음")

    tx = dict(row)
    conn.close()

    tx_type = tx["tx_type"]
    warehouse = tx["warehouse"]
    location = tx["location"]
    to_location = tx.get("to_location", "") or ""
    item_code = tx["item_code"]
    lot_no = tx["lot_no"]
    qty = float(tx["qty"])

    if tx_type == "IN":
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=f"ROLLBACK IN:{tx_id}", block_negative=False)
    elif tx_type == "OUT":
        add_inventory(warehouse, location, "", item_code, "", lot_no, "", qty, remark=f"ROLLBACK OUT:{tx_id}")
    elif tx_type == "MOVE":
        if not to_location:
            raise ValueError("MOVE 기록에 to_location 없음")
        # 역이동
        move_inventory(warehouse, from_location=to_location, to_location=location, item_code=item_code, lot_no=lot_no, qty=qty, remark=f"ROLLBACK MOVE:{tx_id}", block_negative=False)
    else:
        raise ValueError("알 수 없는 tx_type")

# ---------------------------
# 대시보드 요약
# ---------------------------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM history
        WHERE tx_type='IN'
          AND date(created_at)=date('now','localtime')
    """)
    inbound_today = float(cur.fetchone()["v"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM history
        WHERE tx_type='OUT'
          AND date(created_at)=date('now','localtime')
    """)
    outbound_today = float(cur.fetchone()["v"])

    cur.execute("SELECT IFNULL(SUM(qty),0) AS v FROM inventory")
    total_stock = float(cur.fetchone()["v"])

    cur.execute("SELECT COUNT(*) AS c FROM inventory WHERE qty < 0")
    negative_cnt = int(cur.fetchone()["c"])

    conn.close()
    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_cnt": negative_cnt,
    }

# ---------------------------
# 로케이션 스캔 → 해당 위치 재고 리스트
# ---------------------------
def get_location_items(location: str, warehouse: str = "MAIN") -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT warehouse, location, item_code, item_name, lot_no, spec, qty
        FROM inventory
        WHERE warehouse=? AND location=?
        ORDER BY item_code, lot_no
    """, (warehouse, location))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ---------------------------
# 관리자 비번 체크
# ---------------------------
def admin_password_ok(password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT v FROM settings WHERE k='admin_pw_hash'")
    saved = cur.fetchone()
    conn.close()
    if not saved:
        return False
    h = sha256((password or "").encode("utf-8")).hexdigest()
    return h == saved["v"]
