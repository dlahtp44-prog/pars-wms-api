from fastapi import APIRouter
from fastapi.responses import FileResponse
import pandas as pd
from app.db import get_conn

router = APIRouter(prefix="/api/export", tags=["Excel"])

@router.get("/inventory")
def export_inventory():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT warehouse, location, item_code, item_name,
               spec, lot_no, qty, updated_at
        FROM inventory
        ORDER BY location, item_code
    """, conn)
    conn.close()

    path = "/tmp/현재고_현황.xlsx"
    df.to_excel(path, index=False)
    return FileResponse(path, filename="현재고_현황.xlsx")

@router.get("/history")
def export_history():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT created_at, tx_type, warehouse,
               location, item_code, lot_no, qty, remark
        FROM history
        ORDER BY created_at DESC
    """, conn)
    conn.close()

    path = "/tmp/재고_이력.xlsx"
    df.to_excel(path, index=False)
    return FileResponse(path, filename="재고_이력.xlsx")
