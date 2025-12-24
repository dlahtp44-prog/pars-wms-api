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
    qty: float  # 반드시 숫자형
    remark: Optional[str] = "수기"

@router.post("/manual")
async def manual_inbound(data: InboundRequest):
    try:
        db.add_inventory(**data.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        df = pd.read_excel(io.BytesIO(await file.read()))
        # 한글 헤더 매핑
        m = {'창고':'warehouse','로케이션':'location','품번':'item_code','품명':'item_name','LOT':'lot_no','규격':'spec','수량':'qty'}
        df = df.rename(columns=m)
        for _, r in df.iterrows():
            db.add_inventory(str(r.get('warehouse','A')), str(r['location']), str(r['item_code']), 
                             str(r['item_name']), str(r['lot_no']), str(r.get('spec','-')), float(r['qty']), "엑셀")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엑셀 오류: {str(e)}")
