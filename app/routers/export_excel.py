from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv, io
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export")

def csv_response(filename: str, headers: list, rows: list):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    for r in rows:
        writer.writerow([r.get(h, "") for h in headers])
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/inventory")
def export_inventory():
    rows = get_inventory()
    headers = [
        "warehouse","location","brand",
        "item_code","item_name","lot_no","spec","qty"
    ]
    return csv_response("inventory.csv", headers, rows)

@router.get("/history")
def export_history():
    rows = get_history()
    headers = [
        "id","tx_type","warehouse","location",
        "item_code","lot_no","qty","remark","created_at"
    ]
    return csv_response("history.csv", headers, rows)
