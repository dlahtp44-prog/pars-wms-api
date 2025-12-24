from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app import db
import io

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload")
async def upload_inbound_excel(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # 엑셀/CSV 데이터 읽기
        df = pd.read_excel(io.BytesIO(contents))
        
        # 컬럼명 양끝 공백 제거 (불일치 가능성 제거)
        df.columns = [col.strip() for col in df.columns]
        
        # 필수 컬럼 리스트 (업로드하신 TEST.xlsx와 100% 일치)
        required = ['창고', '로케이션', '품번', '품명', 'LOT', '수량']
        
        # 컬럼 존재 여부 체크
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {', '.join(missing)}")

        success_count = 0
        for _, row in df.iterrows():
            # 데이터 형식을 안전하게 변환
            db.add_inventory(
                warehouse=str(row['창고']).strip(),
                location=str(row['로케이션']).strip(),
                item_code=str(row['품번']).strip(),
                item_name=str(row['품명']).strip(),
                lot_no=str(row['LOT']).strip(),
                qty=float(row['수량']), # 숫자로 변환
                brand="-",
                spec="-",
                remark="엑셀 일괄 업로드"
            )
            success_count += 1
            
        return {"message": f"성공: {success_count}건의 재고가 등록되었습니다."}
    
    except Exception as e:
        # 에러 메시지를 상세히 출력하여 디버깅 용이하게 설정
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")
