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
    spec: str = "" # 기본값 빈 문자열 설정으로 에러 방지
    qty: float
    remark: str = ""

@router.post("/manual")
def inbound_manual(data: InboundRequest):
    try:
        db.add_inventory(
            data.warehouse, data.location, data.item_code,
            data.item_name, data.lot_no, data.spec, data.qty, data.remark
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
