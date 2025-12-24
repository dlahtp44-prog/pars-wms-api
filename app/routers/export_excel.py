from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app import db

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/inventory")
def export_inventory():
    try:
        data = db.get_inventory()
        df = pd.DataFrame(data)
        
        # 한글 헤더로 변경
        column_map = {
            'warehouse': '창고', 'location': '로케이션', 'item_code': '품번',
            'item_name': '품명', 'lot_no': 'LOT', 'spec': '규격', 
            'qty': '수량', 'updated_at': '최종업데이트'
        }
        df = df.rename(columns=column_map)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='재고현황')
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=inventory.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def export_history():
    try:
        # limit 없이 전체 이력 가져오기
        data = db.get_history(limit=None) 
        df = pd.DataFrame(data)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="내보낼 데이터가 없습니다.")

        # 한글 헤더 매핑
        column_map = {
            'tx_type': '구분', 'warehouse': '창고', 'location': '로케이션',
            'from_location': '출처', 'to_location': '목적지',
            'item_code': '품번', 'item_name': '품명', 'lot_no': 'LOT',
            'spec': '규격', 'qty': '수량', 'remark': '비고', 'created_at': '일시'
        }
        df = df.rename(columns=column_map)
        
        # 출력 순서 정리 (중요한 정보 위주)
        cols = [c for c in column_map.values() if c in df.columns]
        df = df[cols]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='작업이력')
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=history.xlsx"}
        )
    except Exception as e:
        # 에러 메시지를 로그에 출력하여 디버깅 용이하게 함
        print(f"Excel Export Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
