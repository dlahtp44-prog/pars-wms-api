import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = Path(__file__).parent.parent / "WMS.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _has_column(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r["name"] for r in cur.fetchall()]
    return col in cols

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

    # UPSERT를 위해 UNIQUE 인덱스 필수
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,              -- IN/OUT/MOVE
        warehouse TEXT NOT NULL,
        location TEXT DEFAULT '',           -- IN/OUT 기준 location
        from_location TEXT DEFAULT '',      -- MOVE 출발
        to_location TEXT DEFAULT '',        -- MOVE 도착
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL,
        spec TEXT DEFAULT '',
        qty REAL NOT NULL,
        remark TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 기존 DB에 컬럼 없으면 보강(운영 중 깨짐 방지)
    for col, ddl in [
        ("from_location", "ALTER TABLE history ADD COLUMN from_location TEXT DEFAULT ''"),
        ("to_location",   "ALTER TABLE history ADD COLUMN to_location TEXT DEFAULT ''"),
        ("brand",         "ALTER TABLE history ADD COLUMN brand TEXT DEFAULT ''"),
        ("item_name",     "ALTER TABLE history ADD COLUMN item_name TEXT DEFAULT ''"),
        ("spec",          "ALTER TABLE history ADD COLUMN spec TEXT DEFAULT ''"),
    ]:
        if not _has_column(cur, "history", col):
            cur.execute(ddl)

    conn.commit()
    conn.close()

# ---------- 공통: 이력 기록 ----------
def log_history(
    tx_type: str,
    warehouse: str,
    item_code: str,
    lot_no: str,
    qty: float,
    location: str = "",
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
         brand, item_code, item_name, lot_no, spec, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location, from_location, to_location,
        brand, item_code, item_name, lot_no, spec, qty, remark
    ))
    conn.commit()
    conn.close()

# ---------- 재고 조회 ----------
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
    if q:
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR brand LIKE ?)"
        kw = f"%{q}%"
        params.extend([kw, kw, kw, kw])

    sql += " ORDER BY item_code, lot_no, location"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_location_items(location: str, warehouse: str = "MAIN") -> List[Dict[str, Any]]:
    return get_inventory(warehouse=warehouse, location=location, q=None)

# ---------- 재고 증감(핵심) ----------
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
    if not item_code or not lot_no or not location:
        raise ValueError("item_code/lot_no/location 필수")

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
        tx_type="IN", warehouse=warehouse, location=location,
        brand=brand, item_code=item_code, item_name=item_name,
        lot_no=lot_no, spec=spec, qty=qty, remark=remark
    )

def _current_qty(cur, warehouse: str, location: str, item_code: str, lot_no: str) -> float:
    cur.execute("""
        SELECT IFNULL(qty,0) AS qty
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    r = cur.fetchone()
    return float(r["qty"]) if r else 0.0

def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "출고",
    block_negative: bool = True
):
    if not item_code or not lot_no or not location:
        raise ValueError("item_code/lot_no/location 필수")

    conn = get_conn()
    cur = conn.cursor()

    now_qty = _current_qty(cur, warehouse, location, item_code, lot_no)
    new_qty = now_qty - float(qty)
    if block_negative and new_qty < 0:
        conn.close()
        raise ValueError(f"음수 재고 차단: 현재 {now_qty}, 요청 {qty}")

    # 존재하지 않아도 레코드 생성(차감)되지 않게: inventory가 없으면 에러 처리
    if now_qty == 0 and qty > 0:
        conn.close()
        raise ValueError("재고가 없습니다(0). 먼저 입고 필요")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()

    log_history(
        tx_type="OUT", warehouse=warehouse, location=location,
        item_code=item_code, lot_no=lot_no, qty=qty, remark=remark
    )

def move_inventory(
    warehouse: str,
    item_code: str,
    lot_no: str,
    from_location: str,
    to_location: str,
    qty: float,
    remark: str = "이동",
    block_negative: bool = True
):
    if not item_code or not lot_no or not from_location or not to_location:
        raise ValueError("item_code/lot_no/from/to 필수")

    # 1) 출발지 차감(음수 차단)
    subtract_inventory(
        warehouse=warehouse,
        location=from_location,
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark=f"{remark} 출발({from_location}→{to_location})",
        block_negative=block_negative
    )

    # 2) 도착지 증가(브랜드/품명/규격은 출발지 데이터가 있으면 복사)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT brand, item_name, spec
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, from_location, item_code, lot_no))
    src = cur.fetchone()
    conn.close()

    brand = src["brand"] if src else ""
    item_name = src["item_name"] if src else ""
    spec = src["spec"] if src else ""

    add_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=f"{remark} 도착({from_location}→{to_location})"
    )

    # MOVE 기록(별도)
    log_history(
        tx_type="MOVE", warehouse=warehouse,
        from_location=from_location, to_location=to_location,
        item_code=item_code, lot_no=lot_no, qty=qty,
        remark=remark, brand=brand, item_name=item_name, spec=spec
    )

# ---------- 이력 ----------
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

# ---------- 롤백 ----------
def rollback(tx_id: int, block_negative: bool = True):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise ValueError("기록 없음")

    tx_type = row["tx_type"]
    warehouse = row["warehouse"]
    qty = float(row["qty"])
    item_code = row["item_code"]
    lot_no = row["lot_no"]

    if tx_type == "IN":
        # 입고 롤백 = 동일 위치 차감
        subtract_inventory(warehouse, row["location"], item_code, lot_no, qty, remark="롤백(IN)", block_negative=block_negative)
    elif tx_type == "OUT":
        # 출고 롤백 = 동일 위치 재입고
        add_inventory(warehouse, row["location"], row.get("brand",""), item_code, row.get("item_name",""), lot_no, row.get("spec",""), qty, remark="롤백(OUT)")
    elif tx_type == "MOVE":
        # 이동 롤백 = 반대로 이동
        move_inventory(warehouse, item_code, lot_no, row["to_location"], row["from_location"], qty, remark="롤백(MOVE)", block_negative=block_negative)
    else:
        raise ValueError("지원하지 않는 tx_type")

    log_history(
        tx_type="ROLLBACK",
        warehouse=warehouse,
        location=row.get("location",""),
        from_location=row.get("from_location",""),
        to_location=row.get("to_location",""),
        item_code=item_code,
        lot_no=lot_no,
        qty=qty,
        remark=f"rollback of history.id={tx_id}"
    )

# ---------- 대시보드 ----------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 IN/OUT (localtime)
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM history
        WHERE tx_type='IN'
          AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = float(cur.fetchone()["v"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM history
        WHERE tx_type='OUT'
          AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = float(cur.fetchone()["v"])

    cur.execute("SELECT IFNULL(SUM(qty),0) AS v FROM inventory")
    total_stock = float(cur.fetchone()["v"])

    cur.execute("SELECT COUNT(*) AS c FROM inventory WHERE qty < 0")
    negative_cnt = int(cur.fetchone()["c"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM inventory
        WHERE location='' OR location IS NULL
    """)
    no_location = float(cur.fetchone()["v"])

    conn.close()
    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_cnt": negative_cnt,
        "no_location": no_location
    }
