# app/routers/export_excel.py
import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export", tags=["Export"])

def _csv_response(filename: str, rows: list[dict]):
    if not rows:
        rows = [{}]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/inventory.csv")
def export_inventory(q: str = "", warehouse: str = "", location: str = ""):
    rows = get_inventory(warehouse=warehouse or None, location=location or None, q=q or None)
    return _csv_response("inventory.csv", rows)

@router.get("/history.csv")
def export_history(limit: int = 1000):
    rows = get_history(limit)
    return _csv_response("history.csv", rows)
