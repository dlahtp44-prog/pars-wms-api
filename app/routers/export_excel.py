from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv, io
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/inventory.csv")
def export_inventory_csv():
    rows = get_inventory(limit=200000)

    f = io.StringIO()
    w = csv.writer(f)
    w.writerow(["warehouse","location","brand","item_code","item_name","lot_no","spec","qty","updated_at"])
    for r in rows:
        w.writerow([r["warehouse"], r["location"], r["brand"], r["item_code"], r["item_name"], r["lot_no"], r["spec"], r["qty"], r["updated_at"]])

    f.seek(0)
    return StreamingResponse(
        iter([f.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"}
    )

@router.get("/history.csv")
def export_history_csv():
    rows = get_history(limit=200000)

    f = io.StringIO()
    w = csv.writer(f)
    w.writerow(["id","tx_type","warehouse","location","item_code","item_name","lot_no","spec","qty","remark","meta","created_at"])
    for r in rows:
        w.writerow([r["id"], r["tx_type"], r["warehouse"], r["location"], r["item_code"], r["item_name"], r["lot_no"], r["spec"], r["qty"], r["remark"], r["meta"], r["created_at"]])

    f.seek(0)
    return StreamingResponse(
        iter([f.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=history.csv"}
    )
