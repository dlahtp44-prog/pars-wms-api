from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

# 서버 데이터 수신 규격 정의
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
            warehouse=data.warehouse,
            location=data.location,
            item_code=data.item_code,
            item_name=data.item_name,
            lot_no=data.lot_no,
            spec=data.spec,
            qty=data.qty,
            remark=data.remark
        )
        return {"status": "success", "message": "입고 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        # 한글 헤더 매핑 (TEST.xlsx 기준)
        column_map = {'창고': 'warehouse', '로케이션': 'location', '품번': 'item_code',
                      '품명': 'item_name', 'LOT': 'lot_no', '규격': 'spec', '수량': 'qty'}
        df = df.rename(columns=column_map)
        
        for _, row in df.iterrows():
            db.add_inventory(
                warehouse=str(row.get('warehouse', 'A')),
                location=str(row.get('location', '')).strip(),
                item_code=str(row.get('item_code', '')).strip(),
                item_name=str(row.get('item_name', '')).strip(),
                lot_no=str(row.get('lot_no', '')).strip(),
                spec=str(row.get('spec', '-')).strip(),
                qty=float(row.get('qty', 0)),
                remark="엑셀 업로드"
            )
        return {"status": "success", "message": "업로드 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엑셀 오류: {str(e)}")
