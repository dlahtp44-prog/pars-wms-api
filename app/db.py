import sqlite3

def get_db():
    # 데이터베이스 연결 및 딕셔너리 형태 반환 설정
    conn = sqlite3.connect("wms.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """앱 시작 시 데이터베이스 테이블을 초기화하는 함수"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 재고 테이블 (UNIQUE 제약 조건으로 중복 데이터 합산 처리)
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
    
    # 이력 테이블
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
    print("✅ 데이터베이스 초기화 완료 (init_db)")

# --- 재고 조작 관련 함수 ---

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark=""):
    """입고 및 재고 합산"""
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
    """출고 (재고 차감)"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT qty, item_name, warehouse FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", 
                       (location, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty:
            raise Exception("재고가 부족하거나 존재하지 않는 정보입니다.")
        
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?",
                       (qty, location, item_code, lot_no, spec))
        cursor.execute("DELETE FROM inventory WHERE qty <= 0") # 수량 0이면 삭제
        
        cursor.execute('''
            INSERT INTO history (tx_type, item_code, item_name, lot_no, spec, qty, location, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('OUT', item_code, row['item_name'], lot_no, spec, qty, location, remark))
        conn.commit()
    finally:
        conn.close()

def move_inventory(from_loc, to_loc, item_code, lot_no, spec, qty):
    """재고 이동"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", 
                       (from_loc, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty: raise Exception("이동할 재고가 부족합니다.")

        # 시작 위치 차감
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (qty, from_loc, item_code, lot_no, spec))
        # 도착 위치 추가 (add_inventory 활용)
        add_inventory(row['warehouse'], to_loc, item_code, row['item_name'], lot_no, spec, qty, f"{from_loc}에서 이동")
        conn.commit()
    finally:
        conn.close()

# --- 데이터 조회 관련 함수 ---

def get_inventory():
    conn = get_db()
    data = conn.execute("SELECT * FROM inventory ORDER BY location ASC").fetchall()
    conn.close()
    return data

def get_history():
    conn = get_db()
    data = conn.execute("SELECT * FROM history ORDER BY created_at DESC").fetchall()
    conn.close()
    return data

def dashboard_summary():
    conn = get_db()
    total_items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory").fetchone()[0] or 0
    total_qty = conn.execute("SELECT SUM(qty) FROM inventory").fetchone()[0] or 0
    conn.close()
    return {"total_items": total_items, "total_qty": total_qty}

def get_location_items(location):
    conn = get_db()
    data = conn.execute("SELECT * FROM inventory WHERE location=?", (location,)).fetchall()
    conn.close()
    return data
