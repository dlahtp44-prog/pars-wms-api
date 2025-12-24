import os
import sqlite3
from typing import Optional, List, Dict, Any, Tuple

DB_PATH = os.getenv("DB_PATH", "WMS.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory: (warehouse, location, item_code, lot_no) 유니크
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
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,               -- IN / OUT / MOVE
        warehouse TEXT NOT NULL DEFAULT 'MAIN',
        location TEXT NOT NULL DEFAULT '',
        item_code TEXT NOT NULL DEFAULT '',
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL DEFAULT '',
        spec TEXT DEFAULT '',
        qty REAL NOT NULL DEFAULT 0,
        remark TEXT DEFAULT '',
        meta TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# -------------------------
# history
# -------------------------
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
    meta: str = ""
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark, meta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, item_code, item_name, lot_no, spec, float(qty), remark, meta))
    conn.commit()
    conn.close()

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

# -------------------------
# inventory 조회
# -------------------------
def get_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 5000
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
    params = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    if location is not None and location != "":
        sql += " AND location = ?"
        params.append(location)

    if q:
        sql += """
        AND (
            item_code LIKE ?
            OR item_name LIKE ?
            OR lot_no LIKE ?
            OR brand LIKE ?
            OR spec LIKE ?
        )
        """
        kw = f"%{q}%"
        params.extend([kw, kw, kw, kw, kw])

    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(int(limit))

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# -------------------------
# 핵심 트랜잭션
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
    remark: str = "IN",
):
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty must be > 0")

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            brand=excluded.brand,
            item_name=excluded.item_name,
            spec=excluded.spec,
            qty = qty + excluded.qty,
            updated_at=CURRENT_TIMESTAMP
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))

    conn.commit()
    conn.close()

    log_history("IN", warehouse, location, item_code, item_name, lot_no, spec, qty, remark)

def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "OUT"
):
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty must be > 0")

    conn = get_conn()
    cur = conn.cursor()

    # 현재 수량 확인
    cur.execute("""
        SELECT qty, brand, item_name, spec
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("재고 없음(해당 키)")

    cur_qty = float(row["qty"])
    if cur_qty - qty < 0:
        conn.close()
        raise ValueError("재고 부족(음수 차감 방지)")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()

    log_history("OUT", warehouse, location, item_code, row["item_name"], lot_no, row["spec"], qty, remark)

def move_inventory(
    warehouse: str,
    from_location: str,
    to_location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "MOVE"
):
    qty = float(qty)
    if qty <= 0:
        raise ValueError("qty must be > 0")
    if not from_location or not to_location:
        raise ValueError("from/to location required")

    conn = get_conn()
    cur = conn.cursor()

    # from 재고 확인
    cur.execute("""
        SELECT qty, brand, item_name, spec
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, from_location, item_code, lot_no))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("이동 출발지 재고 없음")

    cur_qty = float(row["qty"])
    if cur_qty - qty < 0:
        conn.close()
        raise ValueError("출발지 재고 부족(음수 방지)")

    # 1) 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    # 2) 목적지 가산(업서트)
    cur.execute("""
        INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            brand=excluded.brand,
            item_name=excluded.item_name,
            spec=excluded.spec,
            qty = qty + excluded.qty,
            updated_at=CURRENT_TIMESTAMP
    """, (warehouse, to_location, row["brand"], item_code, row["item_name"], lot_no, row["spec"], qty))

    conn.commit()
    conn.close()

    meta = f"from={from_location};to={to_location}"
    log_history("MOVE", warehouse, to_location, item_code, row["item_name"], lot_no, row["spec"], qty, remark, meta)

# -------------------------
# 롤백(관리자)
# -------------------------
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (int(tx_id),))
    h = cur.fetchone()
    if not h:
        conn.close()
        raise ValueError("이력 없음")

    tx_type = h["tx_type"]
    warehouse = h["warehouse"]
    location = h["location"]
    item_code = h["item_code"]
    item_name = h["item_name"]
    lot_no = h["lot_no"]
    spec = h["spec"]
    qty = float(h["qty"])
    meta = h["meta"] or ""

    # 롤백 정책:
    # IN  -> subtract same
    # OUT -> add same
    # MOVE -> reverse move (meta에서 from/to 파싱)
    if tx_type == "IN":
        # 입고를 취소 = 해당 location에서 qty만큼 차감(음수 방지)
        conn.close()
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=f"ROLLBACK(IN:{tx_id})")
    elif tx_type == "OUT":
        conn.close()
        add_inventory(warehouse, location, "", item_code, item_name, lot_no, spec, qty, remark=f"ROLLBACK(OUT:{tx_id})")
    elif tx_type == "MOVE":
        # meta: from=...;to=...
        from_loc = ""
        to_loc = ""
        for part in meta.split(";"):
            if part.startswith("from="):
                from_loc = part.replace("from=", "")
            if part.startswith("to="):
                to_loc = part.replace("to=", "")
        if not from_loc or not to_loc:
            conn.close()
            raise ValueError("MOVE meta 파싱 실패")
        conn.close()
        # 원복 = to에서 빼고 from에 더하기
        # (to_location이 history.location 으로 기록되어 있음)
        subtract_inventory(warehouse, to_loc, item_code, lot_no, qty, remark=f"ROLLBACK(MOVE:{tx_id})")
        add_inventory(warehouse, from_loc, "", item_code, item_name, lot_no, spec, qty, remark=f"ROLLBACK(MOVE:{tx_id})")
    else:
        conn.close()
        raise ValueError("지원하지 않는 tx_type")

# -------------------------
# 대시보드
# -------------------------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고/출고 (localtime 기준)
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) s
        FROM history
        WHERE tx_type='IN' AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = float(cur.fetchone()[0])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) s
        FROM history
        WHERE tx_type='OUT' AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = float(cur.fetchone()[0])

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = float(cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative_cnt = int(cur.fetchone()[0])

    conn.close()
    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_cnt": negative_cnt
    }

# -------------------------
# 로케이션 재고 리스트(로케이션 QR 스캔용)
# -------------------------
def get_location_items(warehouse: str, location: str) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at
        FROM inventory
        WHERE warehouse=? AND location=?
        ORDER BY updated_at DESC
    """, (warehouse, location))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# -------------------------
# 관리자 비밀번호(세션용)
# -------------------------
def admin_password_ok(pw: str) -> bool:
    admin_pw = os.getenv("ADMIN_PASSWORD", "1234")  # Railway ENV로 바꾸면 됨
    return (pw or "") == admin_pw
