from fastapi import APIRouter
import csv, io
from fastapi.responses import StreamingResponse
from app.db import get_conn

router = APIRouter(prefix="/api/export")

@router.get("/inventory.xlsx")
def export_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory")
    rows = cur.fetchall()
    conn.close()

    def gen():
        yield "warehouse,location,item_code,item_name,lot_no,spec,qty\n"
        for r in rows:
            yield ",".join(map(str,r))+"\n"

    return StreamingResponse(gen(),
        headers={"Content-Disposition":"attachment; filename=inventory.csv"},
        media_type="text/csv")
