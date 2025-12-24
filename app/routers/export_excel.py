from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import pandas as pd # <-- pip install pandas 필수
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
    else:
        df = pd.read_sql_query("SELECT * FROM history WHERE remark LIKE '%롤백%'", conn)
    conn.close()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={target}.xlsx"})
