from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import csv, io
from app.db import get_inventory, get_history

router = APIRouter(prefix="/export", tags=["다운로드"])

@router.get("/inventory.csv")
def export_inventory_csv():
    rows = get_inventory()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["warehouse","location","brand","item_code","item_name","lot_no","spec","qty","updated_at"])
    for r in rows:
        w.writerow([r["warehouse"],r["location"],r["brand"],r["item_code"],r["item_name"],r["lot_no"],r["spec"],r["qty"],r["updated_at"]])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition":"attachment; filename=inventory.csv"}
    )

@router.get("/history.csv")
def export_history_csv():
    rows = get_history(limit=20000)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id","tx_type","warehouse","location","from_location","to_location","brand","item_code","item_name","lot_no","spec","qty","remark","created_at"])
    for r in rows:
        w.writerow([r.get("id"),r.get("tx_type"),r.get("warehouse"),r.get("location"),
                    r.get("from_location",""),r.get("to_location",""),r.get("brand",""),
                    r.get("item_code"),r.get("item_name",""),r.get("lot_no"),r.get("spec",""),
                    r.get("qty"),r.get("remark",""),r.get("created_at")])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition":"attachment; filename=history.csv"}
    )
