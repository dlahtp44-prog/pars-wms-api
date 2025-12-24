from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

# --- 수기 입고를 위한 데이터 모델 ---
class InboundRequest(BaseModel):
    warehouse: str
    location: str
    item_code: str
    item_name: str
    lot_no: str
    spec: str = "" # 기본값 빈 문자열 설정으로 에러 방지
    qty: float
    remark: str = ""

# 1️⃣ 수기 입고 API
@router.post("/manual")
def inbound_manual(data: InboundRequest):
    try:
        db.add_inventory(
            data.warehouse, data.location, data.item_code,
            data.item_name, data.lot_no, data.spec, data.qty, data.remark
        )
        return {"status": "success", "message": "수기 입고가 완료되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2️⃣ 엑셀 업로드 입고 API
@router.post("/upload")
async def inbound_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # 엑셀 파일 읽기 (openpyxl 엔진 사용 권장)
        df = pd.read_excel(io.BytesIO(contents))
        
        success_count = 0
        for _, row in df.iterrows():
            # 엑셀 컬럼명 매핑 및 데이터 추출
            # 이미지 가이드에 따라 location_name을 창고명으로 활용
            warehouse_val = str(row.get('location_name', 'A'))
            location_val = str(row.get('location', ''))
            item_code_val = str(row.get('item_code', ''))
            item_name_val = str(row.get('item_name', ''))
            lot_no_val = str(row.get('lot_no', ''))
            spec_val = str(row.get('spec', '')) # 규격 반영
            qty_val = float(row.get('qty', 0))

            # 수량이 0보다 큰 경우에만 처리
            if qty_val > 0:
                db.add_inventory(
                    warehouse=warehouse_val,
                    location=location_val,
                    item_code=item_code_val,
                    item_name=item_name_val,
                    lot_no=lot_no_val,
                    spec=spec_val,
                    qty=qty_val,
                    remark="엑셀 업로드"
                )
                success_count += 1
                
        return {
            "status": "success", 
            "message": f"총 {success_count}건의 데이터가 업로드되었습니다."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")
