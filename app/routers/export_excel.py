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
        if not data:
            raise HTTPException(status_code=404, detail="내보낼 재고 데이터가 없습니다.")
            
        df = pd.DataFrame(data)
        
        # 출력 컬럼 정의 및 한글화 (규격 포함)
        column_map = {
            'warehouse': '창고',
            'location': '로케이션',
            'item_code': '품번',
            'item_name': '품명',
            'lot_no': 'LOT',
            'spec': '규격',
            'qty': '수량',
            'updated_at': '최종수정일'
        }
        df = df.rename(columns=column_map)
        
        # 필요한 컬럼만 순서대로 배치
        target_cols = ['창고', '로케이션', '품번', '품명', 'LOT', '규격', '수량', '최종수정일']
        df = df[[c for c in target_cols if c in df.columns]]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='현재고현황')
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=inventory_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def export_history():
    try:
        data = db.get_history(limit=None)
        if not data:
            raise HTTPException(status_code=404, detail="내보낼 이력 데이터가 없습니다.")
            
        df = pd.DataFrame(data)
        
        column_map = {
            'tx_type': '작업구분',
            'warehouse': '창고',
            'item_code': '품번',
            'item_name': '품명',
            'lot_no': 'LOT',
            'spec': '규격',
            'qty': '수량',
            'from_location': '출발지',
            'to_location': '목적지',
            'remark': '비고',
            'created_at': '작업시간'
        }
        df = df.rename(columns=column_map)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='작업이력')
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=history_report.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
