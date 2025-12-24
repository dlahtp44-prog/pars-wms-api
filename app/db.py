import sqlite3

def get_db():
    conn = sqlite3.connect("wms.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT DEFAULT 'A',
            location TEXT NOT NULL,
            item_code TEXT NOT NULL,
            item_name TEXT,
            lot_no TEXT,
            spec TEXT DEFAULT '-',
            qty REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(location, item_code, lot_no, spec)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_type TEXT,
            item_code TEXT,
            item_name TEXT,
            lot_no TEXT,
            spec TEXT,
            qty REAL,
            location TEXT,
            remark TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ 데이터베이스 초기화 완료")

# --- 에러 해결을 위한 검색 및 조회 함수 (수정됨) ---

def get_inventory(q: str = None):
    """검색어(q)를 지원하는 재고 조회"""
    conn = get_db()
    if q:
        query = "SELECT * FROM inventory WHERE item_code LIKE ? OR item_name LIKE ? OR location LIKE ? ORDER BY location ASC"
        rows = conn.execute(query, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM inventory ORDER BY location ASC").fetchall()
    conn.close()
    return rows

def get_history(limit: int = 200):
    """출력 제한(limit)을 지원하는 이력 조회"""
    conn = get_db()
    rows = conn.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows

# --- 관리자 및 기타 로직 ---

def admin_password_ok(password: str) -> bool:
    return password == "1234"

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(location, item_code, lot_no, spec) 
            DO UPDATE SET qty = qty + excluded.qty, updated_at = CURRENT_TIMESTAMP
        ''', (warehouse, location, item_code, item_name, lot_no, spec, qty))
        
        cursor.execute('''
            INSERT INTO history (tx_type, item_code, item_name, lot_no, spec, qty, location, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('IN', item_code, item_name, lot_no, spec, qty, location, remark))
        conn.commit()
    finally:
        conn.close()

def subtract_inventory(location, item_code, lot_no, spec, qty, remark=""):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT qty, item_name FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", 
                       (location, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty: raise Exception("재고 부족")
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (qty, location, item_code, lot_no, spec))
        cursor.execute("DELETE FROM inventory WHERE qty <= 0")
        cursor.execute('''INSERT INTO history (tx_type, item_code, item_name, lot_no, spec, qty, location, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       ('OUT', item_code, row['item_name'], lot_no, spec, qty, location, remark))
        conn.commit()
    finally:
        conn.close()

def move_inventory(from_loc, to_loc, item_code, lot_no, spec, qty):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (from_loc, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty: raise Exception("이동 재고 부족")
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (qty, from_loc, item_code, lot_no, spec))
        add_inventory(row['warehouse'], to_loc, item_code, row['item_name'], lot_no, spec, qty, f"{from_loc} 이동")
        conn.commit()
    finally:
        conn.close()

def dashboard_summary():
    conn = get_db()
    items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory").fetchone()[0] or 0
    qty = conn.execute("SELECT SUM(qty) FROM inventory").fetchone()[0] or 0
    conn.close()
    return {"total_items": items, "total_qty": qty}

def get_location_items(location):
    conn = get_db()
    rows = conn.execute("SELECT * FROM inventory WHERE location=?", (location,)).fetchall()
    conn.close()
    return rows
