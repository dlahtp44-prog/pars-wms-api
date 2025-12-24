from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

# [수기 입고용 데이터 모델] - 프론트엔드와 이 필드명이 정확히 일치해야 422 에러가 안 납니다.
class InboundRequest(BaseModel):
    warehouse: str = "A"
    location: str
    item_code: str
    item_name: str
    lot_no: str
    spec: str = "-"       # 규격 (기본값 설정)
    qty: float            # 수량 (반드시 숫자형)
    remark: Optional[str] = "수기 입고"

@router.post("/manual")
async def manual_inbound(data: InboundRequest):
    """화면에서 직접 입력한 데이터를 DB에 저장"""
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
        return {"status": "success", "message": "입고 처리가 완료되었습니다."}
    except Exception as e:
        print(f"Manual Inbound Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    """엑셀 파일(TEST.xlsx)을 읽어 일괄 입고 처리"""
    try:
        contents = await file.read()
        # 엑셀 읽기 (pandas 사용)
        df = pd.read_excel(io.BytesIO(contents))
        
        # 엑셀 한글 헤더를 DB 필드로 매핑
        column_map = {
            '창고': 'warehouse', '로케이션': 'location', '품번': 'item_code',
            '품명': 'item_name', 'LOT': 'lot_no', '규격': 'spec', '수량': 'qty'
        }
        df = df.rename(columns=column_map)
        
        count = 0
        for _, row in df.iterrows():
            # 데이터 정제 (NaN 처리 및 타입 변환)
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
            count += 1
        return {"status": "success", "message": f"{count}건 업로드 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엑셀 처리 중 오류: {str(e)}")
