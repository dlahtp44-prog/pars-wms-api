from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload")
async def upload_inbound_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx)만 업로드 가능합니다.")
    
    try:
        contents = await file.read()
        # 엑셀 파일 읽기
        df = pd.read_excel(io.BytesIO(contents))
        
        # 컬럼명 앞뒤 공백 제거 (불일치 방지)
        df.columns = [col.strip() for col in df.columns]
        
        # 필수 컬럼 검증
        required = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {', '.join(missing)}")

        success_count = 0
        for _, row in df.iterrows():
            # 데이터 타입을 안전하게 변환하여 DB 저장
            db.add_inventory(
                warehouse=str(row['창고']).strip(),
                location=str(row['로케이션']).strip(),
                item_code=str(row['품번']).strip(),
                item_name=str(row['품명']).strip(),
                lot_no=str(row['LOT']).strip(),
                qty=float(row['수량']),
                brand="-",
                spec="-",
                remark="엑셀 일괄 업로드"
            )
            success_count += 1
            
        return {"message": f"총 {success_count}건의 데이터가 성공적으로 처리되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류 발생: {str(e)}")
