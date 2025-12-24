import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 기존 inventory 테이블에 규격(spec), 창고(warehouse) 포함 확인
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT,
            location TEXT,
            item_code TEXT,
            item_name TEXT,
            lot_no TEXT,
            spec TEXT,
            qty REAL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 관리자 작업 로그 및 롤백용 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_type TEXT, -- IN, OUT, MOVE, ROLLBACK
            warehouse TEXT,
            location TEXT,
            item_code TEXT,
            item_name TEXT,
            lot_no TEXT,
            spec TEXT,
            qty REAL,
            remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark, tx_type="IN"):
    conn = get_db_connection()
    # 1. 재고 반영
    curr = conn.execute(
        "SELECT id, qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
        (warehouse, location, item_code, lot_no)
    ).fetchone()

    if curr:
        new_qty = curr['qty'] + qty
        conn.execute("UPDATE inventory SET qty=?, updated_at=DATETIME('now') WHERE id=?", (new_qty, curr['id']))
    else:
        conn.execute(
            "INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) VALUES (?,?,?,?,?,?,?)",
            (warehouse, location, item_code, item_name, lot_no, spec, qty)
        )
    
    # 2. 관리자 로그 기록 (롤백용)
    conn.execute(
        "INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?)",
        (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark)
    )
    conn.commit()
    conn.close()

# 롤백 핵심 로직
def process_rollback(log_id):
    conn = get_db_connection()
    log = conn.execute("SELECT * FROM audit_logs WHERE id=?", (log_id,)).fetchone()
    if not log: return False

    # 작업의 반대 방향으로 재고 조정
    # 입고(IN)를 롤백하면 출고(-qty) 처리
    adj_qty = -log['qty'] if log['tx_type'] == 'IN' else log['qty']
    
    # 재고 수정
    conn.execute(
        "UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
        (adj_qty, log['warehouse'], log['location'], log['item_code'], log['lot_no'])
    )
    # 로그 삭제 또는 롤백됨 표시
    conn.execute("DELETE FROM audit_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    return True
