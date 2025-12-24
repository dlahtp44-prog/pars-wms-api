# app/db.py
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# Railway/Render에서도 안정적으로 쓰려고 app/data 아래로 고정
DB_PATH = Path("app/data/wms.db")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory: UPSERT를 위해 PK(warehouse, location, item_code, lot_no) 고정
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse   TEXT NOT NULL,
        location    TEXT NOT NULL,
        brand       TEXT,
        item_code   TEXT NOT NULL,
        item_name   TEXT,
        lot_no      TEXT NOT NULL,
        spec        TEXT,
        qty         REAL DEFAULT 0,
        updated_at  TEXT,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type    TEXT NOT NULL,      -- IN / OUT / MOVE
        warehouse  TEXT NOT NULL,
        location   TEXT NOT NULL,      -- MOVE일 때: "FROM→TO"
        item_code  TEXT NOT NULL,
        lot_no     TEXT NOT NULL,
        qty        REAL NOT NULL,
        remark     TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()


# =========================
# 조회
# =========================
def get_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None
) -> List[Dict]:
    conn = get_conn()
    sql = """
        SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at
        FROM inventory
        WHERE 1=1
    """
    params = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    if location:
        sql += " AND location = ?"
        params.append(location)

    if q is not None and q.strip() != "":
        sql += """
          AND (
            item_code LIKE ?
            OR item_name LIKE ?
            OR lot_no LIKE ?
            OR brand LIKE ?
            OR spec LIKE ?
            OR location LIKE ?
          )
        """
        kw = f"%{q.strip()}%"
        params.extend([kw, kw, kw, kw, kw, kw])

    sql += " ORDER BY item_code, lot_no, location"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_history(limit: int = 300) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_location_items(location: str, warehouse: str = "MAIN") -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("""
        SELECT item_code, item_name, lot_no, spec, brand, qty
        FROM inventory
        WHERE warehouse=? AND location=?
        ORDER BY item_code, lot_no
    """, (warehouse, location)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================
# 이력 기록
# =========================
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = ""
):
    conn = get_conn()
    conn.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        tx_type, warehouse, location, item_code, lot_no, float(qty), remark, _now()
    ))
    conn.commit()
    conn.close()


# =========================
# 재고 변경(핵심)
# =========================
def add_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float
):
    conn = get_conn()
    conn.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            brand=excluded.brand,
            item_name=excluded.item_name,
            spec=excluded.spec,
            qty = qty + excluded.qty,
            updated_at=excluded.updated_at
    """, (
        warehouse, location, brand or "",
        item_code, item_name or "",
        lot_no, spec or "",
        float(qty), _now()
    ))
    conn.commit()
    conn.close()


def get_current_qty(warehouse: str, location: str, item_code: str, lot_no: str) -> float:
    conn = get_conn()
    row = conn.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no)).fetchone()
    conn.close()
    return float(row["qty"]) if row else 0.0


def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    block_negative: bool = True
):
    qty = float(qty)
    current = get_current_qty(warehouse, location, item_code, lot_no)

    if block_negative and (current - qty) < 0:
        raise ValueError(f"음수 재고 방지: 현재 {current}, 요청 {qty}")

    conn = get_conn()
    # 존재하지 않으면 0에서 빼면 음수가 될 수 있으니, block_negative가 False일 때만 허용
    if current == 0 and qty != 0:
        # 레코드가 없는데 차감 요청이면, block_negative=True면 위에서 이미 차단됨
        conn.execute("""
            INSERT OR IGNORE INTO inventory
            (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (warehouse, location, "", item_code, "", lot_no, "", 0, _now()))

    conn.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, _now(), warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()


def move_inventory(
    warehouse: str,
    from_location: str,
    to_location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    block_negative: bool = True
):
    # 1) FROM 차감
    subtract_inventory(warehouse, from_location, item_code, lot_no, qty, block_negative=block_negative)
    # 2) TO 증감 (브랜드/품명/규격은 기존 데이터 유지가 어려우니 빈값 허용)
    add_inventory(warehouse, to_location, "", item_code, "", lot_no, "", qty)


# =========================
# 대시보드
# =========================
def dashboard_summary() -> Dict:
    conn = get_conn()
    cur = conn.cursor()

    inbound_today = cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='IN' AND date(created_at)=date('now','localtime')
    """).fetchone()[0]

    outbound_today = cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='OUT' AND date(created_at)=date('now','localtime')
    """).fetchone()[0]

    total_stock = cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM inventory
    """).fetchone()[0]

    negative_count = cur.execute("""
        SELECT COUNT(*) FROM inventory WHERE qty < 0
    """).fetchone()[0]

    no_location = cur.execute("""
        SELECT COUNT(*) FROM inventory WHERE location IS NULL OR location=''
    """).fetchone()[0]

    conn.close()

    return {
        "inbound_today": float(inbound_today),
        "outbound_today": float(outbound_today),
        "total_stock": float(total_stock),
        "negative_count": int(negative_count),
        "no_location": int(no_location),
    }


# =========================
# 롤백(관리자)
# =========================
def rollback(history_id: int) -> bool:
    conn = get_conn()
    cur = conn.cursor()

    row = cur.execute("SELECT * FROM history WHERE id=?", (history_id,)).fetchone()
    if not row:
        conn.close()
        return False

    tx_type = row["tx_type"]
    warehouse = row["warehouse"]
    location = row["location"]
    item_code = row["item_code"]
    lot_no = row["lot_no"]
    qty = float(row["qty"])

    # 반대 작업
    try:
        if tx_type == "IN":
            subtract_inventory(warehouse, location, item_code, lot_no, qty, block_negative=False)
        elif tx_type == "OUT":
            add_inventory(warehouse, location, "", item_code, "", lot_no, "", qty)
        elif tx_type == "MOVE":
            if "→" in location:
                from_loc, to_loc = location.split("→", 1)
                move_inventory(warehouse, to_loc, from_loc, item_code, lot_no, qty, block_negative=False)
    except Exception:
        conn.close()
        raise

    # 이력 삭제
    cur.execute("DELETE FROM history WHERE id=?", (history_id,))
    conn.commit()
    conn.close()
    return True


# =========================
# 관리자 비밀번호
# =========================
def admin_password_ok(pw: str) -> bool:
    # Railway Variables에서 ADMIN_PASSWORD로 관리 권장
    import os
    real = os.getenv("ADMIN_PASSWORD", "admin123")
    return (pw or "") == real
