from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

# 서버 로그에 찍히는 app.routers.inbound와 일치시킴
router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload")
async def upload_inbound_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx)만 업로드 가능합니다.")
    
    try:
        contents = await file.read()
        # TEST.xlsx - Sheet1.csv 구조 분석 결과 반영
        df = pd.read_excel(io.BytesIO(contents))
        
        # 실제 파일 컬럼명과 100% 일치 확인
        required = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        if not all(col in df.columns for col in required):
            raise HTTPException(status_code=400, detail=f"엑셀 양식 오류! 필수 컬럼: {required}")

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
        return {"message": f"총 {len(df)}건 입고 완료!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 처리 실패: {str(e)}")
