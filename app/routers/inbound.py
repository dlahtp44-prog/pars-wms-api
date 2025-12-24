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
