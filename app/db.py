import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "wms.db"

# =========================
# 공통 연결
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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        from_location TEXT,
        to_location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# [내부용] 재고 직접 조작 (히스토리 기록 안함)
# =========================
def _update_stock(cur, warehouse, location, brand, item_code, item_name, lot_no, spec, qty):
    """실제 DB의 재고 수량만 변경하는 내부 함수"""
    cur.execute("""
    INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))

# =========================
# 재고 조회
# =========================
def get_inventory(q: str | None = None):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT warehouse, location, brand,
               item_code, item_name, lot_no, spec,
               SUM(qty) AS qty
        FROM inventory
        WHERE 1=1
    """
    params = []

    if q:
        sql += """
        AND (
            item_code LIKE ?
            OR item_name LIKE ?
            OR lot_no LIKE ?
            OR location LIKE ?
        )
        """
        kw = f"%{q}%"
        params += [kw, kw, kw, kw]

    sql += """
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 입고 (정상 입고용)
# =========================
def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    
    _update_stock(cur, warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    log_history(tx_type="IN", warehouse=warehouse, location=location, 
                item_code=item_code, lot_no=lot_no, qty=qty, remark=remark)
    
    conn.commit()
    conn.close()

# =========================
# 출고 (정상 출고용)
# =========================
def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()

    # 출고는 수량을 음수(-)로 저장하여 _update_stock 호출
    # 기존 코드의 UPDATE 문 대신 일관성을 위해 _update_stock 사용 (브랜드/품명 등은 기존값 유지 위해 빈값 처리 가능)
    cur.execute("""
    UPDATE inventory 
    SET qty = qty - ? 
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    log_history(tx_type="OUT", warehouse=warehouse, location=location, 
                item_code=item_code, lot_no=lot_no, qty=-qty, remark=remark)

    conn.commit()
    conn.close()

# =========================
# 이동
# =========================
def move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()

    # 1. 출발지 차감
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (qty, warehouse, from_location, item_code, lot_no))
    
    # 2. 목적지 가산 (기존 정보 유지를 위해 빈 값으로 INSERT ON CONFLICT)
    cur.execute("""
    INSERT INTO inventory (warehouse, location, item_code, lot_no, qty)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_location, item_code, lot_no, qty))

    log_history("MOVE", warehouse, from_location, to_location, item_code, lot_no, qty, "이동")

    conn.commit()
    conn.close()

# =========================
# 이력 관리
# =========================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark, to_location=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history (tx_type, warehouse, location, to_location, item_code, lot_no, qty, remark, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, to_location, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_history(limit=200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 롤백 (이력 기반 역연산)
# =========================
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        return

    # 롤백 시에는 log_history를 호출하지 않는 직접 SQL 실행
    if h["tx_type"] == "IN":
        cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                    (h["qty"], h["warehouse"], h["location"], h["item_code"], h["lot_no"]))
    elif h["tx_type"] == "OUT":
        cur.execute("UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                    (abs(h["qty"]), h["warehouse"], h["location"], h["item_code"], h["lot_no"]))
    elif h["tx_type"] == "MOVE":
        # 보낸 곳은 다시 늘리고, 받은 곳은 다시 줄임
        cur.execute("UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                    (h["qty"], h["warehouse"], h["location"], h["item_code"], h["lot_no"]))
        cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                    (h["qty"], h["warehouse"], h["to_location"], h["item_code"], h["lot_no"]))

    # 사용된 히스토리 삭제 (선택 사항: 삭제 대신 '취소됨' 마킹을 권장하지만 여기선 간단히 삭제)
    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    
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

    # SQLite의 date('now')는 UTC 기준일 수 있으므로 주의 필요
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN' AND date(created_at) = date('now', 'localtime')
    """)
    inbound = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT' AND date(created_at) = date('now', 'localtime')
    """)
    outbound = abs(cur.fetchone()[0])

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0]

    conn.close()
    return {
        "inbound_today": inbound,
        "outbound_today": outbound,
        "total_stock": total,
        "negative_stock": negative
    }

# =========================
# 기타 기능
# =========================
def get_location_items(location: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT item_code, item_name, lot_no, spec, qty FROM inventory WHERE location=? ORDER BY item_code", (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def admin_password_ok(pw: str) -> bool:
    return pw == "admin123"
