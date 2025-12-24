from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

router = APIRouter(prefix="/api/export", tags=["엑셀"])

try:
    import pandas as pd
except ImportError:
    pd = None

from app.db import get_inventory, get_history


@router.get("/inventory")
def export_inventory():
    if not pd:
        raise HTTPException(500, "pandas 미설치")

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
    if not pd:
        raise HTTPException(500, "pandas 미설치")

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
