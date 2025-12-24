from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

# 'app.routers.inbound'로 등록되는 루터입니다.
router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload")
async def upload_inbound_excel(file: UploadFile = File(...)):
    # 파일 확장자 검사
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일만 업로드 가능합니다.")
    
    try:
        contents = await file.read()
        # 데이터 시트 읽기
        df = pd.read_excel(io.BytesIO(contents))
        
        # 사용자가 제공한 TEST.xlsx 구조와 일치하는지 검증
        required_cols = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(status_code=400, detail=f"엑셀 양식이 틀립니다. 필수 항목: {', '.join(required_cols)}")
        
        success_count = 0
        for _, row in df.iterrows():
            # DB 저장 로직 (db.py 내 add_inventory 함수 호출)
            db.add_inventory(
                warehouse=str(row['창고']),
                location=str(row['로케이션']),
                item_code=str(row['품번']),
                item_name=str(row['품명']),
                lot_no=str(row['LOT']),
                qty=float(row['수량']),
                brand="-", # 기본값 처리
                spec="-",  # 기본값 처리
                remark="엑셀 일괄 입고"
            )
            success_count += 1
            
        return {"message": f"총 {success_count}건의 품목이 성공적으로 입고되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")
