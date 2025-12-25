# app/routers/export_excel.py
import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export", tags=["Export"])

def _csv_response(filename: str, rows: list):
    if not rows:
        rows = []
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/inventory")
def export_inventory():
    rows = get_inventory("")
    return _csv_response("inventory.csv", rows)

@router.get("/history")
def export_history():
    rows = get_history(limit=5000, q="")
    return _csv_response("history.csv", rows)
