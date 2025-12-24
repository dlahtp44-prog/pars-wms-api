from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.db import get_conn, add_inventory, subtract_inventory

router = APIRouter(prefix="/api/excel", tags=["Excel"])

@router.get("/download/{target}")
async def download_excel(target: str):
    conn = get_conn()
    if target == "inventory":
        df = pd.read_sql_query("SELECT * FROM inventory WHERE qty != 0", conn)
    elif target == "history":
        df = pd.read_sql_query("SELECT * FROM history", conn)
    elif target == "rollback":
        df = pd.read_sql_query("SELECT * FROM history WHERE remark LIKE '%롤백%'", conn)
    conn.close()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f"attachment; filename={target}_export.xlsx"})

@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents)) if file.filename.endswith('.csv') else pd.read_excel(io.BytesIO(contents))
    for _, row in df.iterrows():
        t = str(row['type']).upper()
        if t == 'IN':
            add_inventory(row['warehouse'], row['location'], row.get('brand',''), row['item_code'], 
                          row['item_name'], str(row.get('lot_no','')), row.get('spec',''), row['qty'], "엑셀업로드")
        elif t == 'OUT':
            subtract_inventory(row['warehouse'], row['location'], row['item_code'], str(row.get('lot_no','')), row['qty'], "엑셀업로드")
    return {"msg": "성공적으로 처리되었습니다."}
