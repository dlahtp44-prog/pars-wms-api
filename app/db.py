import sqlite3

def get_db():
    conn = sqlite3.connect("wms.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """테이블 초기화 및 UNIQUE 제약 조건 설정 확인"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 재고 테이블 (spec 포함 유니크 설정)
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

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark=""):
    """재고 합산 및 입고 이력 생성"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 1. 재고 Upsert (합산)
        cursor.execute('''
            INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(location, item_code, lot_no, spec) 
            DO UPDATE SET 
                qty = qty + excluded.qty,
                updated_at = CURRENT_TIMESTAMP
        ''', (warehouse, location, item_code, item_name, lot_no, spec, qty))
        
        # 2. 입고 이력(History) 저장
        cursor.execute('''
            INSERT INTO history (tx_type, item_code, item_name, lot_no, spec, qty, location, remark)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('IN', item_code, item_name, lot_no, spec, qty, location, remark))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
