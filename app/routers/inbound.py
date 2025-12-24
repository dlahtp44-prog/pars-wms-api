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
    spec: str = ""
    qty: float
    remark: str = ""

@router.post("/manual")
def inbound_manual(data: InboundRequest):
    try:
        db.add_inventory(
            data.warehouse, data.location, data.item_code,
            data.item_name, data.lot_no, data.spec, data.qty, data.remark
        )
        return {"status": "success", "message": "수기 입고 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def inbound_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        count = 0
        for _, row in df.iterrows():
            # 이미지 컬럼 가이드를 준수하여 매핑
            warehouse_val = str(row.get('location_name', '기본창고'))
            location_val = str(row.get('location', row.get('location_name', '미지정')))
            item_code_val = str(row.get('item_code', ''))
            item_name_val = str(row.get('item_name', ''))
            lot_no_val = str(row.get('lot_no', ''))
            spec_val = str(row.get('spec', ''))
            qty_val = float(row.get('qty', 0))
            brand_val = str(row.get('brand', ''))

            if qty_val > 0:
                db.add_inventory(
                    warehouse=warehouse_val,
                    location=location_val,
                    item_code=item_code_val,
                    item_name=item_name_val,
                    lot_no=lot_no_val,
                    spec=spec_val,
                    qty=qty_val,
                    remark=f"업로드(Brand:{brand_val})"
                )
                count += 1
        return {"status": "success", "message": f"{count}건 데이터 처리 완료(규격 포함)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 에러: {str(e)}")
