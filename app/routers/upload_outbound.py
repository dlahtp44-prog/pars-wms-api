from fastapi import APIRouter, UploadFile, File
import csv, io
from fastapi.responses import JSONResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/upload", tags=["업로드"])

@router.post("/outbound")
def upload_outbound(file: UploadFile = File(...)):
    try:
        content = file.file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        for r in reader:
            warehouse = r.get("warehouse") or r.get("창고") or "MAIN"
            location  = r.get("location")  or r.get("로케이션") or ""
            item_code = r.get("item_code") or r.get("품번") or ""
            lot_no    = r.get("lot_no")    or r.get("LOT") or r.get("LOT NO") or ""
            qty       = float(r.get("qty") or r.get("수량") or 0)

            subtract_inventory(warehouse, location, item_code, lot_no, qty, remark="CSV 출고 업로드", block_negative=True)

        return {"ok": True, "msg": "출고 CSV 업로드 완료"}
    except Exception as e:
        return JSONResponse({"ok": False, "detail": str(e)}, status_code=400)
