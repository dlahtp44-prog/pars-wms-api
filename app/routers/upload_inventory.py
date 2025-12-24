from fastapi import APIRouter, UploadFile, File
import csv, io
from app.db import add_inventory

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.post("/inventory")
def upload_inventory(file: UploadFile = File(...)):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))

    count = 0
    for r in reader:
        warehouse = r.get("warehouse","MAIN")
        location  = r.get("location","")
        brand     = r.get("brand","")
        item_code = r.get("item_code","")
        item_name = r.get("item_name","")
        lot_no    = r.get("lot_no","")
        spec      = r.get("spec","")
        qty       = float(r.get("qty",0) or 0)
        if not item_code or not lot_no or not location or qty <= 0:
            continue
        add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="CSV IN")
        count += 1

    return {"ok": True, "rows": count}
