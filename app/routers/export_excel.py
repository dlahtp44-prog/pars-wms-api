# app/routers/export_excel.py
from fastapi import APIRouter
from fastapi.responses import Response
import csv, io
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export", tags=["export"])

def _csv_response(filename: str, rows: list, headers: list):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow([r.get(h, "") for h in headers])
    data = buf.getvalue().encode("utf-8-sig")  # Excel 호환 BOM
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/inventory")
def export_inventory():
    rows = get_inventory()
    headers = ["warehouse","location","brand","item_code","item_name","lot_no","spec","qty","updated_at"]
    return _csv_response("inventory.csv", rows, headers)

@router.get("/history")
def export_history():
    rows = get_history(2000)
    headers = ["id","tx_type","warehouse","location","from_location","to_location","brand",
               "item_code","item_name","lot_no","spec","qty","remark","created_at"]
    return _csv_response("history.csv", rows, headers)
