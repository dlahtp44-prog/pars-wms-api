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
            raise HTTPException(status_code=404, detail="데이터 없음")
            
        df = pd.DataFrame(data)
        column_map = {
            'warehouse': '창고', 'location': '로케이션', 'item_code': '품번',
            'item_name': '품명', 'lot_no': 'LOT', 'spec': '규격', 
            'qty': '수량', 'updated_at': '업데이트일시'
        }
        df = df.rename(columns=column_map)
        
        # 컬럼 순서 고정
        cols = ['창고', '로케이션', '품번', '품명', 'LOT', '규격', '수량', '업데이트일시']
        df = df[[c for c in cols if c in df.columns]]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='현재고')
        
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=inventory.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
