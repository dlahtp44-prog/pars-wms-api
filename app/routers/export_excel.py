from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import pandas as pd
import io
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export", tags=["엑셀"])

@router.get("/inventory")
def export_inventory():
    rows = get_inventory()
    df = pd.DataFrame(rows)

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=inventory.xlsx"}
    )

@router.get("/history")
def export_history():
    rows = get_history(5000)
    df = pd.DataFrame(rows)

    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=history.xlsx"}
    )
