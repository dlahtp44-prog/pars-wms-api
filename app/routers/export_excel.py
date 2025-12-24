from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.db import get_conn

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/{target}")
async def export_excel(target: str):
    conn = get_conn()
    if target == "inventory":
        df = pd.read_sql_query("SELECT * FROM inventory WHERE qty != 0", conn)
    elif target == "history":
        df = pd.read_sql_query("SELECT * FROM history", conn)
    elif target == "rollback":
        # 롤백 이력만 추출 (예시: remark에 '롤백'이 포함된 경우)
        df = pd.read_sql_query("SELECT * FROM history WHERE remark LIKE '%롤백%'", conn)
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid target")
    
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=target)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={target}_report.xlsx"}
    )
