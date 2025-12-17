# app/db.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "wms.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 재고 테이블 (최종 통합)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item TEXT PRIMARY KEY,
        brand TEXT,
        name TEXT,
        lot TEXT,
        spec TEXT,
        warehouse TEXT,
        location TEXT,
        qty INTEGER
    )
    """)

    # 작업 이력
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        item TEXT,
        qty INTEGER,
        warehouse TEXT,
        location TEXT,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def log_history(type, item, qty, warehouse, location, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (type, item, qty, warehouse, location, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        type, item, qty, warehouse, location,
        remark, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()
