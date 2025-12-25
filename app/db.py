import sqlite3
from datetime import datetime
from typing import List, Dict

DB_PATH = "wms.db"


# =========================
# DB 연결
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# DB 초기화
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        updated_at TEXT
    );

    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no);

    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        from_location TEXT,
        to_location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        remark TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password TEXT
    );
    """)

    # 기본 관리자 비밀번호
    cur.execute("SELECT COUNT(*) FROM admin")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admin(password) VALUES ('1234')")

    conn.commit()
    conn.close()


# =========================
# 재고 조회
# =========================
def get_inventory(q: str = "") -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()

    if q:
        cur.execute("""
            SELECT * FROM inventory
            WHERE item_code LIKE ? OR item_name LIKE ?
            ORDER BY location
        """, (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM inventory ORDER BY location")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 입고
# =========================
def add_inventory(
    warehouse, location, brand,
    item_code, item_name, lot_no, spec, qty
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty,
            updated_at = excluded.updated_at
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no, spec, qty,
        datetime.now().isoformat()
    ))

    log_history(
        "IN", warehouse, location,
        None, None,
        item_code, item_name, lot_no, spec, qty,
        "입고"
    )

    conn.commit()
    conn.close()


# =========================
# 출고
# =========================
def subtract_inventory(
    warehouse, location,
    item_code, lot_no, qty,
    block_negative: bool = True
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    if not row:
        raise ValueError("재고 없음")

    if block_negative and row["qty"] < qty:
        raise ValueError("재고 부족")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?, updated_at=?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        qty, datetime.now().isoformat(),
        warehouse, location, item_code, lot_no
    ))

    log_history(
        "OUT", warehouse, location,
        None, None,
        item_code, "", lot_no, "", qty,
        "출고"
    )

    conn.commit()
    conn.close()


# =========================
# 이동
# =========================
def move_inventory(
    warehouse,
    from_location, to_location,
    item_code, lot_no, qty
):
    subtract_inventory(
        warehouse, from_location,
        item_code, lot_no, qty,
        block_negative=True
    )

    add_inventory(
        warehouse, to_location, "",
        item_code, "", lot_no, "", qty
    )

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, from_location, to_location,
         item_code, lot_no, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "MOVE", warehouse, from_location, to_location,
        item_code, lot_no, qty,
        "이동",
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


# =========================
# 이력
# =========================
def get_history() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (history_id,))
    h = cur.fetchone()
    if not h:
        raise ValueError("이력 없음")

    if h["tx_type"] == "IN":
        subtract_inventory(
            h["warehouse"], h["location"],
            h["item_code"], h["lot_no"], h["qty"],
            block_negative=False
        )

    elif h["tx_type"] == "OUT":
        add_inventory(
            h["warehouse"], h["location"], "",
            h["item_code"], h["item_name"],
            h["lot_no"], h["spec"], h["qty"]
        )

    cur.execute("DELETE FROM history WHERE id=?", (history_id,))
    conn.commit()
    conn.close()


# =========================
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN' AND date(created_at)=date('now')
    """)
    inbound = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT' AND date(created_at)=date('now')
    """)
    outbound = cur.fetchone()[0]

    conn.close()
    return inbound, outbound, total


# =========================
# 로케이션 관련 (🔥 여기 때문에 에러 났던 부분)
# =========================
def get_locations() -> List[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT location
        FROM inventory
        ORDER BY location
    """)
    rows = [r["location"] for r in cur.fetchall()]
    conn.close()
    return rows


def get_location_items(location: str) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM inventory
        WHERE location=?
        ORDER BY item_code
    """, (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 관리자
# =========================
def admin_password_ok(password: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admin WHERE password=?", (password,))
    ok = cur.fetchone() is not None
    conn.close()
    return ok
