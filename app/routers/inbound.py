from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

# ... 기존 manual 입고 로직 유지 ...

@router.post("/upload")
async def upload_inbound_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다.")
    
    try:
        # 엑셀 읽기
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 필수 컬럼 확인
        required_cols = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        for col in required_cols:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"필수 컬럼이 누락되었습니다: {col}")
        
        success_count = 0
        for _, row in df.iterrows():
            # DB 저장 (db.py의 add_inventory 활용)
            db.add_inventory(
                warehouse=str(row['창고']),
                location=str(row['로케이션']),
                brand=str(row.get('브랜드', '')),
                item_code=str(row['품번']),
                item_name=str(row['품명']),
                lot_no=str(row['LOT']),
                spec=str(row.get('규격', '')),
                qty=float(row['수량']),
                remark="엑셀 일괄 입고"
            )
            success_count += 1
            
        return {"message": f"{success_count}건의 품목이 성공적으로 입고되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"업로드 중 오류 발생: {str(e)}")
