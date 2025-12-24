from fastapi import APIRouter, Response
import pandas as pd
from app import db
import io
from datetime import datetime
import urllib.parse  # 한글 파일명 인코딩용

router = APIRouter(prefix="/api/export", tags=["Excel Export"])

@router.get("/{target}")
async def export_excel(target: str):
    try:
        if target == "inventory":
            data = db.get_inventory()
            base_name = "재고현황"
        elif target == "history":
            data = db.get_history_for_excel()
            base_name = "작업이력"
        else:
            return Response(content="Invalid target", status_code=400)

        if not data:
            return Response(content="데이터가 없습니다.", status_code=404)

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        # 한글 파일명을 브라우저가 인식할 수 있도록 인코딩
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{base_name}_{timestamp}.xlsx"
        encoded_filename = urllib.parse.quote(filename)
        
        headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
        
        return Response(
            content=output.getvalue(), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            headers=headers
        )
    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)
