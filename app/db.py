# app/db.py
import os
import sqlite3
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple

DB_PATH = Path(__file__).parent.parent / "WMS.db"
BLOCK_NEGATIVE = os.getenv("BLOCK_NEGATIVE_STOCK", "1") == "1"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

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
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # UPSERT용 UNIQUE (없으면 ON CONFLICT가 안 먹음)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,              -- IN/OUT/MOVE_IN/MOVE_OUT
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        item_code TEXT NOT NULL,
        lot_no TEXT NOT NULL,
        qty REAL NOT NULL,
        remark TEXT DEFAULT '',
        ref TEXT DEFAULT '',                -- move ref 등
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# ---------- 조회 ----------
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
      SUM(qty) as qty
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
    if q is not None:
        kw = f"%{q.strip()}%"
        sql += """
        AND (
          item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR spec LIKE ?
          OR location LIKE ? OR warehouse LIKE ?
        )
        """
        params.extend([kw, kw, kw, kw, kw, kw])

    sql += """
    GROUP BY warehouse, location, item_code, lot_no
    ORDER BY item_code, lot_no, warehouse, location
    """

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history(limit: int = 300) -> List[Dict[str, Any]]:
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

# ---------- 이력 ----------
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "",
    ref: str = ""
) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history(tx_type, warehouse, location, item_code, lot_no, qty, remark, ref)
        VALUES(?,?,?,?,?,?,?,?)
    """, (tx_type, warehouse, location, item_code, lot_no, float(qty), remark, ref))
    tx_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(tx_id)

# ---------- 재고 조작(입고/출고/이동 공용) ----------
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
) -> None:
    qty = float(qty)
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
          brand=excluded.brand,
          item_name=excluded.item_name,
          spec=excluded.spec,
          qty = inventory.qty + excluded.qty,
          updated_at=CURRENT_TIMESTAMP
    """, (warehouse, location, brand or "", item_code, item_name or "", lot_no, spec or "", qty))

    conn.commit()
    conn.close()

    log_history("IN", warehouse, location, item_code, lot_no, qty, remark)

def _current_qty(cur, warehouse: str, location: str, item_code: str, lot_no: str) -> float:
    cur.execute("""
      SELECT IFNULL(SUM(qty),0)
      FROM inventory
      WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    return float(cur.fetchone()[0])

def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "OUT"
) -> None:
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty must be > 0")

    conn = get_conn()
    cur = conn.cursor()

    cur_qty = _current_qty(cur, warehouse, location, item_code, lot_no)
    new_qty = cur_qty - qty
    if BLOCK_NEGATIVE and new_qty < 0:
        conn.close()
        raise ValueError(f"음수 재고 차단: 현재 {cur_qty}, 출고요청 {qty}")

    # inventory 테이블은 "행 단위 누적"이 아니라 한 행에 qty를 쌓는 구조로 쓰고 있음(UPSERT)
    # 따라서 UPDATE로 qty 감소
    cur.execute("""
      UPDATE inventory
      SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
      WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    # 혹시 기존 행이 없다면(신규 출고) insert 후 음수 가능
    if cur.rowcount == 0:
        if BLOCK_NEGATIVE:
            conn.close()
            raise ValueError("재고가 없어 출고 불가")
        cur.execute("""
          INSERT INTO inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
          VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        """, (warehouse, location, "", item_code, "", lot_no, "", -qty))

    conn.commit()
    conn.close()

    log_history("OUT", warehouse, location, item_code, lot_no, qty, remark)

def move_inventory(
    warehouse: str,
    item_code: str,
    lot_no: str,
    qty: float,
    from_location: str,
    to_location: str,
    remark: str = "MOVE"
) -> None:
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty must be > 0")
    ref = f"{from_location}->{to_location}"

    # from 차감
    subtract_inventory(warehouse, from_location, item_code, lot_no, qty, remark=f"{remark} OUT")
    # to 증가(브랜드/품명/spec은 from행에서 가져오면 좋지만, 여기선 최소로)
    add_inventory(warehouse, to_location, "", item_code, "", lot_no, "", qty, remark=f"{remark} IN")

    # MOVE로도 한 줄 남기고 싶으면 추가 기록(선택)
    log_history("MOVE", warehouse, to_location, item_code, lot_no, qty, remark=remark, ref=ref)

# ---------- 롤백 ----------
def rollback(tx_id: int) -> None:
    """
    history 한 줄을 역으로 되돌림:
    IN  -> 재고 감소
    OUT -> 재고 증가
    MOVE/MOVE_IN/MOVE_OUT -> 단순화(여기서는 MOVE를 OUT/IN로 이미 남겨서, MOVE는 기록만)
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (int(tx_id),))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("기록 없음")

    tx_type = row["tx_type"]
    warehouse = row["warehouse"]
    location = row["location"]
    item_code = row["item_code"]
    lot_no = row["lot_no"]
    qty = float(row["qty"])

    conn.close()

    if tx_type == "IN":
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=f"ROLLBACK IN#{tx_id}")
    elif tx_type == "OUT":
        add_inventory(warehouse, location, "", item_code, "", lot_no, "", qty, remark=f"ROLLBACK OUT#{tx_id}")
    else:
        # MOVE는 이미 OUT/IN으로 반영되므로, 여기서는 안전하게 “지원 안함” 처리
        raise ValueError("MOVE 롤백은 OUT/IN 기록으로 처리하세요(또는 정책 확정 필요)")

# ---------- 대시보드 ----------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고/출고 (localtime)
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
    negative_rows = int(cur.fetchone()[0])

    # 간단 그래프용: 상위 10 품번 합
    cur.execute("""
      SELECT item_code, IFNULL(SUM(qty),0) as qty
      FROM inventory
      GROUP BY item_code
      ORDER BY qty DESC
      LIMIT 10
    """)
    top_items = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_rows": negative_rows,
        "top_items": top_items,
    }

# ---------- 관리자 비번 ----------
def admin_password_ok(pw: str) -> bool:
    admin_pw = os.getenv("ADMIN_PASSWORD", "1234")  # Railway Variables로 꼭 바꾸기
    return (pw or "") == admin_pw
