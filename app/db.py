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

def move_inventory(from_loc, to_loc, item_code, lot_no, spec, qty):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (from_loc, item_code, lot_no, spec))
        row = cursor.fetchone()
        if not row or row['qty'] < qty: raise Exception("이동할 재고가 부족합니다.")
        
        cursor.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=? AND spec=?", (qty, from_loc, item_code, lot_no, spec))
        add_inventory(row['warehouse'], to_loc, item_code, row['item_name'], lot_no, spec, qty, f"{from_loc}에서 이동")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_inventory(q=None):
    conn = get_db()
    if q:
        return conn.execute("SELECT * FROM inventory WHERE item_code LIKE ? OR item_name LIKE ?", (f"%{q}%", f"%{q}%")).fetchall()
    return conn.execute("SELECT * FROM inventory ORDER BY location ASC").fetchall()

def get_history(limit=200):
    conn = get_db()
    return conn.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()

def admin_password_ok(pw): return pw == "1234"
def dashboard_summary():
    conn = get_db()
    res = conn.execute("SELECT COUNT(DISTINCT item_code), SUM(qty) FROM inventory").fetchone()
    return {"total_items": res[0] or 0, "total_qty": res[1] or 0}
