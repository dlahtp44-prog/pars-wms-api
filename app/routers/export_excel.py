from fastapi import APIRouter, Response
import pandas as pd
from app import db
import io
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["Excel Export"])

@router.get("/{target}")
async def export_excel(target: str):
    # target 종류: inventory, history, admin
    table_name = "history" if target in ["history", "admin"] else "inventory"
    data = db.get_all_data(table_name)
    
    if not data:
        return {"message": "데이터가 없습니다."}

    df = pd.DataFrame(data)
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    filename = f"{target}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
