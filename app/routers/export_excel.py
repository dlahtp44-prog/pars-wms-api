from fastapi import APIRouter, Response
import pandas as pd
from app import db
import io
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["Excel Export"])

@router.get("/{target}")
async def export_excel(target: str):
    if target == "inventory":
        data = db.get_inventory()
        filename = f"재고현황_{datetime.now().strftime('%Y%m%d')}.xlsx"
    else: # history 혹은 admin
        data = db.get_history_for_excel()
        filename = f"작업이력_{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    if not data:
        return {"message": "데이터가 없습니다."}

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
