from fastapi import APIRouter, Response
import pandas as pd
from app import db
import io
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["Excel Export"])

@router.get("/{target}")
async def export_excel(target: str):
    try:
        if target == "inventory":
            # 현재고 데이터 가져오기
            data = db.get_inventory()
            filename = f"재고현황_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        elif target == "history":
            # 작업 이력 데이터 가져오기 (db.py에 구현된 get_history_for_excel 사용)
            data = db.get_history_for_excel()
            filename = f"작업이력_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        else:
            return {"error": "Invalid target"}

        if not data:
            return Response(content="데이터가 없습니다.", status_code=404)

        # 데이터프레임 생성 및 엑셀 변환
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
        return Response(
            content=output.getvalue(), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers=headers
        )
    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)
