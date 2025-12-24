from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app import db
import pandas as pd
import io

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

# 프론트엔드에서 보낸 JSON을 검증하는 모델
class InboundSchema(BaseModel):
    warehouse: str
    location: str
    item_code: str
    item_name: str
    lot_no: str
    spec: str = "-"
    qty: float
    remark: Optional[str] = ""

@router.post("/manual")
async def manual_inbound(data: InboundSchema):
    try:
        # 데이터베이스 저장 함수 호출
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
        print(f"Manual Inbound Error: {str(e)}") # 서버 로그 확인용
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    """엑셀 업로드 처리 (TEST.xlsx 양식 대응)"""
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        column_map = {
            '창고': 'warehouse', '로케이션': 'location', '품번': 'item_code',
            '품명': 'item_name', 'LOT': 'lot_no', '규격': 'spec', '수량': 'qty'
        }
        df = df.rename(columns=column_map)
        
        for _, row in df.iterrows():
            db.add_inventory(
                warehouse=str(row['warehouse']),
                location=str(row['location']),
                item_code=str(row['item_code']),
                item_name=str(row['item_name']),
                lot_no=str(row['lot_no']),
                spec=str(row.get('spec', '-')),
                qty=float(row['qty']),
                remark="엑셀 업로드"
            )
        return {"message": "업로드 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
