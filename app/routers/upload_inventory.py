from fastapi import APIRouter, UploadFile, File
import csv, io
from fastapi.responses import JSONResponse
from app.db import add_inventory

router = APIRouter(prefix="/api/upload", tags=["업로드"])

@router.post("/inventory")
def upload_inventory(file: UploadFile = File(...)):
    try:
        content = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        for r in reader:
            warehouse = r.get("warehouse") or r.get("창고") or "MAIN"
            location  = r.get("location")  or r.get("로케이션") or ""
            brand     = r.get("brand")     or r.get("브랜드") or ""
            item_code = r.get("item_code") or r.get("품번") or ""
            item_name = r.get("item_name") or r.get("품명") or ""
            lot_no    = r.get("lot_no")    or r.get("LOT") or r.get("LOT NO") or ""
            spec      = r.get("spec")      or r.get("규격") or ""
            qty       = float(r.get("qty") or r.get("수량") or 0)

            add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="CSV 입고 업로드")

        return {"ok": True, "msg": "입고 CSV 업로드 완료"}
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)
