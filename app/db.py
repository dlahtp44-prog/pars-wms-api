import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "WMS.db"

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
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location TEXT NOT NULL DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL DEFAULT '',
        spec TEXT DEFAULT '',
        qty REAL NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

    # history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,                   -- IN / OUT / MOVE
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location TEXT NOT NULL DEFAULT '',       -- MOVE면 "from→to" 요약 저장
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL DEFAULT '',
        spec TEXT DEFAULT '',
        qty REAL NOT NULL DEFAULT 0,
        remark TEXT DEFAULT '',
        rolled_back INTEGER NOT NULL DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# -------------------------
# 공용: 이력 기록
# -------------------------
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    brand: str = "",
    item_name: str = "",
    spec: str = "",
    remark: str = "",
    from_location: str = "",
    to_location: str = "",
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location,
         brand, item_code, item_name, lot_no, spec, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location, from_location, to_location,
        brand, item_code, item_name, lot_no, spec, qty, remark
    ))
    conn.commit()
    conn.close()

# -------------------------
# 재고 UPSERT 증가
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
    remark: str = "",
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
          brand=excluded.brand,
          item_name=excluded.item_name,
          spec=excluded.spec,
          qty = inventory.qty + excluded.qty,
          updated_at=CURRENT_TIMESTAMP
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))
    conn.commit()
    conn.close()

    log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        brand=brand,
        item_name=item_name,
        spec=spec,
        remark=remark or "입고"
    )

# -------------------------
# 재고 차감 (부족하면 에러)
# -------------------------
def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "",
    brand: str = "",
    item_name: str = "",
    spec: str = "",
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS q
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    have = float(cur.fetchone()["q"])

    if have < qty:
        conn.close()
        raise ValueError(f"재고 부족: 현재 {have}, 요청 {qty}")

    # 기존 행 qty 감소 (해당 unique key 행이 1개라 가정)
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()

    log_history(
        tx_type="OUT",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        brand=brand,
        item_name=item_name,
        spec=spec,
        remark=remark or "출고"
    )

# -------------------------
# 이동 (from 차감 + to 증가)
# -------------------------
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
    remark: str = "",
):
    # from 차감
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS q
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, from_location, item_code, lot_no))
    have = float(cur.fetchone()["q"])
    if have < qty:
        conn.close()
        raise ValueError(f"이동 재고 부족: 현재 {have}, 요청 {qty}")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    # to 증가 (UPSERT)
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
          brand=excluded.brand,
          item_name=excluded.item_name,
          spec=excluded.spec,
          qty = inventory.qty + excluded.qty,
          updated_at=CURRENT_TIMESTAMP
    """, (warehouse, to_location, brand, item_code, item_name, lot_no, spec, qty))

    conn.commit()
    conn.close()

    log_history(
        tx_type="MOVE",
        warehouse=warehouse,
        location=f"{from_location}→{to_location}",
        from_location=from_location,
        to_location=to_location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        brand=brand,
        item_name=item_name,
        spec=spec,
        remark=remark or "이동"
    )

# -------------------------
# 조회
# -------------------------
def get_inventory(warehouse: Optional[str]=None, location: Optional[str]=None, q: Optional[str]=None) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT
          warehouse, location, brand, item_code, item_name, lot_no, spec,
          ROUND(SUM(qty), 3) AS qty
        FROM inventory
        WHERE 1=1
    """
    params = []
    if warehouse:
        sql += " AND warehouse=?"
        params.append(warehouse)
    if location:
        sql += " AND location=?"
        params.append(location)
    if q is not None and q.strip() != "":
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR brand LIKE ? OR spec LIKE ?)"
        kw = f"%{q.strip()}%"
        params += [kw, kw, kw, kw, kw]

    sql += """
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code, lot_no, warehouse, location
    """
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history(limit: int = 500, include_rolled_back: bool=False) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    if include_rolled_back:
        cur.execute("""SELECT * FROM history ORDER BY id DESC LIMIT ?""", (limit,))
    else:
        cur.execute("""SELECT * FROM history WHERE rolled_back=0 ORDER BY id DESC LIMIT ?""", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# -------------------------
# 롤백
# -------------------------
def rollback(tx_id: int) -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("이력 없음")

    if int(row["rolled_back"]) == 1:
        conn.close()
        raise ValueError("이미 롤백된 건입니다")

    tx_type = row["tx_type"]
    warehouse = row["warehouse"]
    item_code = row["item_code"]
    lot_no = row["lot_no"]
    qty = float(row["qty"])
    brand = row["brand"] or ""
    item_name = row["item_name"] or ""
    spec = row["spec"] or ""

    # 역연산
    try:
        if tx_type == "IN":
            # IN을 취소 => 같은 키에서 qty 감소 (부족하면 에러)
            subtract_inventory(warehouse, row["location"], item_code, lot_no, qty,
                               remark=f"롤백(IN#{tx_id})", brand=brand, item_name=item_name, spec=spec)

        elif tx_type == "OUT":
            # OUT을 취소 => 다시 더하기
            add_inventory(warehouse, row["location"], brand, item_code, item_name, lot_no, spec, qty,
                          remark=f"롤백(OUT#{tx_id})")

        elif tx_type == "MOVE":
            # MOVE 취소 => 반대로 이동
            from_loc = row["from_location"] or ""
            to_loc = row["to_location"] or ""
            if not from_loc or not to_loc:
                raise ValueError("MOVE 롤백 불가(출발/도착 정보 없음)")
            # 원래 to에서 빼고 from에 더하기
            # to에서 빼기
            subtract_inventory(warehouse, to_loc, item_code, lot_no, qty,
                               remark=f"롤백(MOVE#{tx_id})-to차감", brand=brand, item_name=item_name, spec=spec)
            # from에 더하기
            add_inventory(warehouse, from_loc, brand, item_code, item_name, lot_no, spec, qty,
                          remark=f"롤백(MOVE#{tx_id})-from복원")
        else:
            raise ValueError("알 수 없는 tx_type")
    finally:
        # 위 함수들이 각각 log_history를 남기므로, 원본 이력은 rolled_back=1로 표시
        pass

    # 원본 이력 rolled_back 처리
    cur.execute("UPDATE history SET rolled_back=1 WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()

    return {"ok": True, "rolled_back_id": tx_id}

# -------------------------
# 대시보드
# -------------------------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS s
        FROM history
        WHERE rolled_back=0 AND tx_type='IN'
          AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = float(cur.fetchone()["s"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS s
        FROM history
        WHERE rolled_back=0 AND tx_type='OUT'
          AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = float(cur.fetchone()["s"])

    cur.execute("SELECT IFNULL(SUM(qty),0) AS s FROM inventory")
    total_stock = float(cur.fetchone()["s"])

    cur.execute("SELECT COUNT(*) AS c FROM inventory WHERE qty < 0")
    negative_stock = int(cur.fetchone()["c"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS s
        FROM inventory
        WHERE location IS NULL OR location=''
    """)
    no_location = float(cur.fetchone()["s"])

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative_stock,
        "no_location": no_location
    }

# -------------------------
# 관리자 비밀번호
# -------------------------
def admin_password_ok(pw: str) -> bool:
    # Railway 변수 ADMIN_PASSWORD로 설정 권장
    admin_pw = os.getenv("ADMIN_PASSWORD", "1234")
    return (pw or "") == admin_pw
