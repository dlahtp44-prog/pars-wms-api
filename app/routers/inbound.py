from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

# 기존에 등록된 app.routers.inbound와 경로가 겹치지 않도록 prefix를 확인합니다.
router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload")
async def upload_inbound_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx)만 업로드 가능합니다.")
    
    try:
        contents = await file.read()
        # TEST.xlsx 구조 읽기
        df = pd.read_excel(io.BytesIO(contents))
        
        # 필수 컬럼 검증 (사용자 파일 기준)
        required = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        if not all(col in df.columns for col in required):
            raise HTTPException(status_code=400, detail="엑셀 양식이 틀립니다. (필수: 창고, 로케이션, 품번, 품명, LOT, 수량)")

        success_count = 0
        for _, row in df.iterrows():
            db.add_inventory(
                warehouse=str(row['창고']),
                location=str(row['로케이션']),
                item_code=str(row['품번']),
                item_name=str(row['품명']),
                lot_no=str(row['LOT']),
                qty=float(row['수량']),
                brand="-",
                spec="-",
                remark="엑셀 일괄 업로드"
            )
            success_count += 1
            
        return {"message": f"총 {success_count}건의 데이터가 성공적으로 처리되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")
