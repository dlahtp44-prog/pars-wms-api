from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

class InboundRequest(BaseModel):
    warehouse: str
    location: str
    item_code: str
    item_name: str
    lot_no: str
    spec: str = "" # 기본값 설정
    qty: float
    remark: str = ""

@router.post("/manual")
def inbound_manual(data: InboundRequest):
    try:
        db.add_inventory(data.warehouse, data.location, data.item_code, data.item_name, data.lot_no, data.spec, data.qty, data.remark)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def inbound_upload(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    for _, row in df.iterrows():
        db.add_inventory(
            warehouse=str(row.get('location_name', 'A')),
            location=str(row.get('location', '')),
            item_code=str(row.get('item_code', '')),
            item_name=str(row.get('item_name', '')),
            lot_no=str(row.get('lot_no', '')),
            spec=str(row.get('spec', '')), # 엑셀 규격 반영
            qty=float(row.get('qty', 0)),
            remark="업로드 입고"
        )
    return {"status": "success"}
