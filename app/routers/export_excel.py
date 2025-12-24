from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.db import get_conn

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/{target}")
async def export_excel_target(target: str):
    conn = get_conn()
    if target == "inventory":
        query = "SELECT * FROM inventory WHERE qty != 0"
    elif target == "history":
        query = "SELECT * FROM history"
    elif target == "rollback":
        query = "SELECT * FROM history WHERE remark LIKE '%롤백%'"
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid target")
    
    df = pd.read_sql_query(query, conn)
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
