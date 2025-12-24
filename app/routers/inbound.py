from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    """
    사용자가 업로드한 엑셀(TEST.xlsx) 양식을 읽어 재고에 추가합니다.
    양식: 창고, 로케이션, 품번, 품명, LOT, 규격, 수량
    """
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.")

    try:
        # 1. 엑셀 파일 읽기
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # 2. 한글 컬럼명을 DB 영문 필드명으로 매핑
        # 보내주신 TEST.xlsx 양식의 헤더와 정확히 일치시켰습니다.
        column_map = {
            '창고': 'warehouse',
            '로케이션': 'location',
            '품번': 'item_code',
            '품명': 'item_name',
            'LOT': 'lot_no',
            '규격': 'spec',
            '수량': 'qty'
        }
        
        # 엑셀에 필요한 컬럼이 모두 있는지 확인
        missing_cols = [col for col in column_map.keys() if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400, 
                detail=f"엑셀 양식이 올바르지 않습니다. 누락된 컬럼: {', '.join(missing_cols)}"
            )

        # 컬럼 이름 변경
        df = df.rename(columns=column_map)

        # 3. 데이터 클리닝 및 DB 저장
        success_count = 0
        for _, row in df.iterrows():
            # 빈 값 처리 (NaN을 빈 문자열이나 0으로 변환)
            warehouse = str(row.get('warehouse', 'A')).strip()
            location = str(row.get('location', '')).strip()
            item_code = str(row.get('item_code', '')).strip()
            item_name = str(row.get('item_name', '')).strip()
            lot_no = str(row.get('lot_no', '')).strip()
            
            # 규격(Spec) 처리: 특수문자가 많으므로 문자열로 강제 변환하고 결측치는 '-'로 표시
            spec = str(row.get('spec', '-')).strip()
            if spec == 'nan': spec = '-'
            
            # 수량 처리: 숫자가 아닌 경우 0으로 처리
            try:
                qty = float(row.get('qty', 0))
            except:
                qty = 0

            # 필수 데이터(품번, 로케이션)가 있는 경우에만 저장
            if item_code and location:
                db.add_inventory(
                    warehouse=warehouse,
                    location=location,
                    item_code=item_code,
                    item_name=item_name,
                    lot_no=lot_no,
                    spec=spec,
                    qty=qty,
                    remark="엑셀 업로드"
                )
                success_count += 1

        return {"message": f"총 {success_count}건의 데이터가 성공적으로 업로드되었습니다."}

    except Exception as e:
        print(f"Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류 발생: {str(e)}")

@router.post("/manual")
async def manual_inbound(data: dict):
    """
    수기 입고 처리 (화면에서 직접 입력)
    """
    try:
        db.add_inventory(
            warehouse=data.get('warehouse', 'A'),
            location=data.get('location'),
            item_code=data.get('item_code'),
            item_name=data.get('item_name'),
            lot_no=data.get('lot_no'),
            spec=data.get('spec', '-'),
            qty=float(data.get('qty', 0)),
            remark=data.get('remark', '수기 입고')
        )
        return {"message": "입고 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
