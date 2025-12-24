from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload") # 실제 경로는 /api/inbound/upload가 됩니다.
async def upload_inbound_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다.")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 필수 컬럼 검증
        required = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        if not all(col in df.columns for col in required):
            raise HTTPException(status_code=400, detail="엑셀 양식이 올바르지 않습니다. 필수 컬럼을 확인하세요.")

        for _, row in df.iterrows():
            db.add_inventory(
                warehouse=str(row['창고']),
                location=str(row['로케이션']),
                brand=str(row.get('브랜드', '-')),
                item_code=str(row['품번']),
                item_name=str(row['품명']),
                lot_no=str(row['LOT']),
                spec=str(row.get('규격', '-')),
                qty=float(row['수량']),
                remark="엑셀 대량 입고"
            )
        return {"message": f"총 {len(df)}건 입고 완료!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
