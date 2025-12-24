from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

# 수기 입고 데이터 모델
class InboundRequest(BaseModel):
    warehouse: str
    location: str
    item_code: str
    item_name: str
    lot_no: str
    spec: str = ""
    qty: float
    remark: str = ""

# [수정] 수기 입고 API
@router.post("/manual")
def inbound_manual(data: InboundRequest):
    try:
        db.add_inventory(
            data.warehouse, data.location, data.item_code,
            data.item_name, data.lot_no, data.spec, data.qty, data.remark
        )
        return {"status": "success", "message": "입고 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 엑셀 업로드 입고 API
@router.post("/upload")
async def inbound_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 필수 컬럼 확인 (창고, 로케이션, 품번, 품명, LOT, 수량)
        required = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        for col in required:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {col}")

        count = 0
        for _, row in df.iterrows():
            # 규격은 선택사항
            spec = str(row.get('규격', ''))
            db.add_inventory(
                str(row['창고']), str(row['로케이션']), str(row['품번']),
                str(row['품명']), str(row['LOT']), spec, float(row['수량']), "엑셀 업로드"
            )
            count += 1
            
        return {"status": "success", "message": f"{count}건 입고 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
