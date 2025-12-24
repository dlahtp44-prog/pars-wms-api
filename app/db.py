import sqlite3

def get_db():
    conn = sqlite3.connect("wms.db")
    conn.row_factory = sqlite3.Row
    return conn

# 1. 입고 (Inbound)
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

# 2. 출고 (Outbound)
def subtract_inventory(location, item_code, lot_no, spec, qty, remark=""):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT qty, item_name, warehouse FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", 
                       (location, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty:
            raise Exception("재고가 부족하거나 존재하지 않습니다.")
        
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?",
                       (qty, location, item_code, lot_no, spec))
        cursor.execute("DELETE FROM inventory WHERE qty <= 0")
        
        cursor.execute('''
            INSERT INTO history (tx_type, item_code, item_name, lot_no, spec, qty, location, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('OUT', item_code, row['item_name'], lot_no, spec, qty, location, remark))
        conn.commit()
    finally:
        conn.close()

# 3. 이동 (Move)
def move_inventory(from_loc, to_loc, item_code, lot_no, spec, qty):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 출고 처리와 동일하게 소스 로케이션 차감
        cursor.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", 
                       (from_loc, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty: raise Exception("이동할 재고가 부족합니다.")

        # 차감 및 추가
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (qty, from_loc, item_code, lot_no, spec))
        add_inventory(row['warehouse'], to_loc, item_code, row['item_name'], lot_no, spec, qty, f"{from_loc}에서 이동")
        conn.commit()
    finally:
        conn.close()

# 4. 조회용 함수들 (에러 발생했던 부분들)
def get_inventory():
    conn = get_db()
    data = conn.execute("SELECT * FROM inventory").fetchall()
    conn.close()
    return data

def get_history():
    conn = get_db()
    data = conn.execute("SELECT * FROM history ORDER BY created_at DESC").fetchall()
    conn.close()
    return data

def dashboard_summary():
    conn = get_db()
    total_items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory").fetchone()[0]
    total_qty = conn.execute("SELECT SUM(qty) FROM inventory").fetchone()[0] or 0
    conn.close()
    return {"total_items": total_items, "total_qty": total_qty}

def get_location_items(location):
    conn = get_db()
    data = conn.execute("SELECT * FROM inventory WHERE location=?", (location,)).fetchall()
    conn.close()
    return data
