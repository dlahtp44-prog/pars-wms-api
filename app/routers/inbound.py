from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

class InboundRequest(BaseModel):
    warehouse: str = "A"
    location: str
    item_code: str
    item_name: str
    lot_no: str
    spec: str = "-"
    qty: float
    remark: Optional[str] = "수기 입고"

@router.post("/manual")
async def manual_inbound(data: InboundRequest):
    try:
        db.add_inventory(
            warehouse=data.warehouse, location=data.location,
            item_code=data.item_code, item_name=data.item_name,
            lot_no=data.lot_no, spec=data.spec, qty=data.qty, remark=data.remark
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        # 헤더 매핑
        m = {'창고':'warehouse','로케이션':'location','품번':'item_code','품명':'item_name','LOT':'lot_no','규격':'spec','수량':'qty'}
        df = df.rename(columns=m)
        for _, r in df.iterrows():
            db.add_inventory(str(r.get('warehouse','A')), str(r['location']), str(r['item_code']), 
                             str(r['item_name']), str(r['lot_no']), str(r.get('spec','-')), float(r['qty']), "엑셀")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
