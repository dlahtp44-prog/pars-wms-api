import os
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import io

from fastapi import FastAPI, Body, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# 엑셀 업로드용
try:
    import openpyxl
except ImportError:
    openpyxl = None

# ---------------------- 설정 ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "WMS.db")

app = FastAPI(title="PARS WMS QR BUTTON FINAL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- DB 유틸 ----------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # 품목 마스터
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
          item_code TEXT PRIMARY KEY,
          item_name TEXT,
          spec      TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # 로케이션 마스터
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          warehouse TEXT NOT NULL,
          location  TEXT NOT NULL,
          UNIQUE(warehouse, location)
        )
        """
    )

    # 재고/거래 이력 테이블
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_tx (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tx_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          tx_type TEXT NOT NULL, 
          warehouse TEXT NOT NULL,
          location  TEXT NOT NULL,
          item_code TEXT NOT NULL,
          item_name TEXT,
          lot_no    TEXT NOT NULL,
          qty       REAL NOT NULL,
          remark    TEXT,
          source_tx_id INTEGER,
          UNIQUE(id, tx_type)
        )
        """
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_item_wh_loc_lot ON inventory_tx (item_code, warehouse, location, lot_no)")

    conn.commit()
    conn.close()


init_db()

# ---------------------- 지원 함수 ----------------------
def upsert_item(item_code, item_name):
    conn = get_conn()
    cur = conn.cursor()
    item_name_to_use = item_name if item_name else None
    cur.execute(
        """
        INSERT INTO items (item_code, item_name)
        VALUES (?, ?)
        ON CONFLICT(item_code) DO UPDATE SET item_name=excluded.item_name
        """,
        (item_code, item_name_to_use)
    )
    conn.commit()
    conn.close()


def normalize_lot(lot: Optional[str]) -> str:
    if lot is None:
        return "없음"
    lot_str = str(lot).strip()
    return lot_str if lot_str else "없음"


def get_item_name_by_code(item_code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT item_name FROM items WHERE item_code = ?", (item_code,))
    row = cur.fetchone()
    conn.close()
    return row["item_name"] if row else ""


# ---------------------- 모델 ----------------------
class Location(BaseModel):
    warehouse: str
    location: str

class InventoryTx(BaseModel):
    warehouse: str
    location: str
    item_code: str
    item_name: Optional[str] = None
    lot_no: Optional[str] = None
    qty: float = Field(..., ge=0)
    remark: Optional[str] = None

class MoveTx(BaseModel):
    warehouse_from: str
    location_from: str
    warehouse_to: str
    location_to: str
    item_code: str
    lot_no: str
    qty: float = Field(..., gt=0)
    remark: Optional[str] = None


# ---------------------- 입고 ----------------------
@app.post("/api/inventory/in")
def api_inbound(data: InventoryTx):
    conn = get_conn()
    cur = conn.cursor()

    upsert_item(data.item_code, data.item_name)
    item_name_final = get_item_name_by_code(data.item_code)
    lot_no = normalize_lot(data.lot_no)

    cur.execute(
        """
        INSERT INTO inventory_tx (tx_type, warehouse, location, item_code, item_name, lot_no, qty, remark)
        VALUES ('IN', ?, ?, ?, ?, ?, ?, ?)
        """,
        (data.warehouse, data.location, data.item_code, item_name_final, lot_no, data.qty, data.remark or "입고")
    )
    conn.commit()

    cur.execute(
        """
        SELECT SUM(qty) AS current_qty FROM inventory_tx
        WHERE warehouse = ? AND location = ? AND item_code = ? AND lot_no = ?
        """,
        (data.warehouse, data.location, data.item_code, lot_no)
    )
    current_qty = cur.fetchone()["current_qty"]
    conn.close()

    return {"result": "OK", "msg": "입고 완료", "현재고": current_qty}


# ---------------------- 출고 ----------------------
@app.post("/api/inventory/out")
def api_outbound(data: InventoryTx):
    conn = get_conn()
    cur = conn.cursor()

    lot_no = normalize_lot(data.lot_no)
    cur.execute(
        """
        SELECT SUM(qty) AS current_qty FROM inventory_tx
        WHERE warehouse = ? AND location = ? AND item_code = ? AND lot_no = ?
        """,
        (data.warehouse, data.location, data.item_code, lot_no)
    )
    current_qty = cur.fetchone()["current_qty"] or 0

    if current_qty < data.qty:
        conn.close()
        return {"result": "FAIL", "msg": "재고 부족", "현재고": current_qty}

    item_name_final = get_item_name_by_code(data.item_code)

    cur.execute(
        """
        INSERT INTO inventory_tx (tx_type, warehouse, location, item_code, item_name, lot_no, qty, remark)
        VALUES ('OUT', ?, ?, ?, ?, ?, ?, ?)
        """,
        (data.warehouse, data.location, data.item_code, item_name_final, lot_no, -data.qty, data.remark or "출고")
    )
    conn.commit()
    conn.close()

    return {"result": "OK", "msg": "출고 완료", "출고후잔량": current_qty - data.qty}


# ---------------------- 이동 ----------------------
@app.post("/api/inventory/move")
def api_move(data: MoveTx):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT SUM(qty) AS current_qty FROM inventory_tx
        WHERE warehouse = ? AND location = ? AND item_code = ? AND lot_no = ?
        """,
        (data.warehouse_from, data.location_from, data.item_code, data.lot_no)
    )
    current_qty = cur.fetchone()["current_qty"] or 0

    if current_qty < data.qty:
        conn.close()
        return {"result": "FAIL", "msg": "이동 재고 부족", "현재고": current_qty}

    item_name_final = get_item_name_by_code(data.item_code)

    # 출고
    cur.execute(
        """
        INSERT INTO inventory_tx (tx_type, warehouse, location, item_code, item_name, lot_no, qty, remark)
        VALUES ('MOVE', ?, ?, ?, ?, ?, ?, ?)
        """,
        (data.warehouse_from, data.location_from, data.item_code, item_name_final, data.lot_no, -data.qty, 
         f"이동 출고 ({data.warehouse_to}/{data.location_to}) - {data.remark or ''}")
    )

    # 입고
    cur.execute(
        """
        INSERT INTO inventory_tx (tx_type, warehouse, location, item_code, item_name, lot_no, qty, remark)
        VALUES ('MOVE', ?, ?, ?, ?, ?, ?, ?)
        """,
        (data.warehouse_to, data.location_to, data.item_code, item_name_final, data.lot_no, data.qty, 
         f"이동 입고 ({data.warehouse_from}/{data.location_from}) - {data.remark or ''}")
    )
    conn.commit()
    conn.close()

    return {"result": "OK", "msg": "이동 완료"}


# ---------------------- 기초재고 ----------------------
@app.post("/api/opening")
def api_opening(data: InventoryTx):
    conn = get_conn()
    cur = conn.cursor()

    upsert_item(data.item_code, data.item_name)
    item_name_final = get_item_name_by_code(data.item_code)
    lot_no = normalize_lot(data.lot_no)

    cur.execute(
        """
        INSERT INTO inventory_tx (tx_type, warehouse, location, item_code, item_name, lot_no, qty, remark)
        VALUES ('OPENING', ?, ?, ?, ?, ?, ?, ?)
        """,
        (data.warehouse, data.location, data.item_code, item_name_final, lot_no, data.qty, data.remark or "기초재고")
    )
    conn.commit()

    cur.execute(
        """
        SELECT SUM(qty) AS current_qty FROM inventory_tx
        WHERE warehouse = ? AND location = ? AND item_code = ? AND lot_no = ?
        """,
        (data.warehouse, data.location, data.item_code, lot_no)
    )
    current_qty = cur.fetchone()["current_qty"]
    conn.close()

    return {"result": "OK", "msg": "기초재고 입력 완료", "현재고": current_qty}


# ---------------------- 롤백 ----------------------
@app.post("/api/rollback")
def api_rollback(tx_id: int = Query(...)):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM inventory_tx WHERE id = ?", (tx_id,))
    original_tx = cur.fetchone()

    if not original_tx:
        conn.close()
        raise HTTPException(status_code=404, detail="거래 ID를 찾을 수 없습니다.")

    if original_tx["tx_type"] == "ROLLBACK":
        conn.close()
        raise HTTPException(status_code=400, detail="이미 취소된 거래입니다.")

    rollback_qty = -original_tx["qty"]

    if rollback_qty < 0:
        cur.execute(
            """
            SELECT SUM(qty) AS current_qty FROM inventory_tx
            WHERE warehouse = ? AND location = ? AND item_code = ? AND lot_no = ?
            """,
            (original_tx["warehouse"], original_tx["location"], original_tx["item_code"], original_tx["lot_no"])
        )
        current_qty = cur.fetchone()["current_qty"] or 0

        if current_qty + rollback_qty < 0:
            conn.close()
            raise HTTPException(status_code=400, detail=f"취소 시 재고가 부족합니다. 현재 재고: {current_qty}")

    cur.execute(
        """
        INSERT INTO inventory_tx 
        (tx_type, warehouse, location, item_code, item_name, lot_no, qty, remark, source_tx_id)
        VALUES ('ROLLBACK', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            original_tx["warehouse"],
            original_tx["location"],
            original_tx["item_code"],
            original_tx["item_name"],
            original_tx["lot_no"],
            rollback_qty,
            f"TX_ID={tx_id} 롤백",
            tx_id
        )
    )
    conn.commit()
    conn.close()

    return {"result": "OK", "msg": f"거래 ID {tx_id} 롤백 완료"}


# ---------------------- Location API ----------------------
@app.post("/api/location")
def api_create_location(data: Location):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO locations (warehouse, location) VALUES (?, ?)",
            (data.warehouse, data.location)
        )
        conn.commit()
        return {"id": cur.lastrowid, "msg": "Location 등록 완료"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 존재하는 창고/Location 조합입니다.")
    finally:
        conn.close()


@app.get("/api/location")
def api_location_list():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM locations ORDER BY warehouse, location")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.delete("/api/location/{id}")
def api_delete_location(id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM locations WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"msg": "Location 삭제 완료"}


# ---------------------- 재고 조회 ----------------------
@app.get("/api/inventory")
def api_inventory_view(
    item_code: Optional[str] = Query(None),
    lot_no: Optional[str] = Query(None),
    warehouse: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    conn = get_conn()
    cur = conn.cursor()

    where_clauses = []
    params = []

    if item_code:
        where_clauses.append("t.item_code LIKE ?")
        params.append(f"%{item_code}%")
    if lot_no:
        where_clauses.append("t.lot_no LIKE ?")
        params.append(f"%{lot_no}%")
    if warehouse:
        where_clauses.append("t.warehouse LIKE ?")
        params.append(f"%{warehouse}%")
    if location:
        where_clauses.append("t.location LIKE ?")
        params.append(f"%{location}%")

    if date_from:
        where_clauses.append("t.tx_time >= ?")
        params.append(date_from)
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            next_day = dt_to + timedelta(days=1)
            where_clauses.append("t.tx_time < ?")
            params.append(next_day.strftime("%Y-%m-%d"))
        except:
            where_clauses.append("t.tx_time < ?")
            params.append(date_to)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    sql = f"""
        SELECT
            t.warehouse,
            t.location,
            t.item_code,
            t.item_name,
            t.lot_no,
            SUM(t.qty) AS current_qty,
            (SELECT MAX(tx_time) FROM inventory_tx 
             WHERE warehouse=t.warehouse AND location=t.location 
             AND item_code=t.item_code AND lot_no=t.lot_no) AS last_tx_time
        FROM inventory_tx t
        {where_sql}
        GROUP BY t.warehouse, t.location, t.item_code, t.lot_no, t.item_name
        HAVING SUM(t.qty) > 0
        ORDER BY t.warehouse, t.location, t.item_code, t.lot_no
    """

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ---------------------- 수량 조회 ----------------------
@app.get("/api/inventory/qty")
def api_inventory_qty_view(
    item_code: str = Query(...),
    warehouse: str = Query(...),
    location: str = Query(...),
    lot_no: str = Query(...)
):
    lot_no_normalized = normalize_lot(lot_no)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT SUM(qty) AS current_qty FROM inventory_tx
        WHERE warehouse = ? AND location = ? AND item_code = ? AND lot_no = ?
        """,
        (warehouse, location, item_code, lot_no_normalized)
    )
    current_qty = cur.fetchone()["current_qty"] or 0
    conn.close()

    return {"current_qty": current_qty}


# ---------------------- 이력 조회 ----------------------
@app.get("/api/history")
def api_history_view(
    tx_type: Optional[str] = Query(None),
    item_code: Optional[str] = Query(None),
    lot_no: Optional[str] = Query(None),
    warehouse: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    conn = get_conn()
    cur = conn.cursor()

    where_clauses = []
    params = []

    if tx_type:
        where_clauses.append("tx_type = ?")
        params.append(tx_type)
    if item_code:
        where_clauses.append("item_code LIKE ?")
        params.append(f"%{item_code}%")
    if lot_no:
        where_clauses.append("lot_no LIKE ?")
        params.append(f"%{lot_no}%")
    if warehouse:
        where_clauses.append("warehouse LIKE ?")
        params.append(f"%{warehouse}%")
    if location:
        where_clauses.append("location LIKE ?")
        params.append(f"%{location}%")

    if date_from:
        where_clauses.append("tx_time >= ?")
        params.append(date_from)
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d")
            next_day = dt_to + timedelta(days=1)
            where_clauses.append("tx_time < ?")
            params.append(next_day.strftime("%Y-%m-%d"))
        except:
            where_clauses.append("tx_time < ?")
            params.append(date_to)

    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    sql = f"""
        SELECT
            id,
            strftime('%Y-%m-%d %H:%M:%S', tx_time) AS tx_time,
            tx_type,
            warehouse,
            location,
            item_code,
            item_name,
            lot_no,
            qty,
            remark,
            source_tx_id
        FROM inventory_tx
        {where_sql}
        ORDER BY id DESC
    """

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ---------------------- 품명 조회 ----------------------
@app.get("/api/item_name")
def get_item_name_api(item_code: str = Query(...)):
    item_name = get_item_name_by_code(item_code)
    return {"item_name": item_name}


# ---------------------- STATIC 파일 제공 ----------------------

# 메인 대시보드 (home)
@app.get("/")
def index_page():
    return FileResponse("static/index.html")

# 입고 페이지
@app.get("/inbound")
def inbound_page():
    return FileResponse("static/inbound.html")

# 출고 페이지
@app.get("/outbound")
def outbound_page():
    return FileResponse("static/outbound.html")

# 이동 페이지
@app.get("/move")
def move_page():
    return FileResponse("static/move.html")

# 재고 조회 페이지
@app.get("/inventory")
def inventory_page():
    return FileResponse("static/inventory.html")

# 거래 이력 조회 페이지
@app.get("/history")
def history_page():
    return FileResponse("static/history.html")



