from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import subtract_inventory

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post("/outbound")
def upload_outbound(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    count = 0
    for r in reader:
        warehouse = r.get("warehouse","MAIN")
        location  = r.get("location","")
        item_code = r.get("item_code","")
        lot_no    = r.get("lot_no","")
        qty       = float(r.get("qty",0) or 0)
        if not item_code or not lot_no or not location or qty <= 0:
            continue
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark="CSV OUT")
        count += 1

    return {"ok": True, "rows": count}
