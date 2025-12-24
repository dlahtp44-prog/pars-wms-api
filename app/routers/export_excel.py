import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.db import get_inventory, get_history

router = APIRouter(prefix="/api/export", tags=["엑셀/다운로드"])

def _csv_response(filename: str, header: list, rows: list):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(h, "") for h in header])

    data = buf.getvalue().encode("utf-8-sig")  # 엑셀 한글 깨짐 방지
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/inventory.csv")
def export_inventory():
    rows = get_inventory()
    header = ["warehouse","location","brand","item_code","item_name","lot_no","spec","qty","updated_at"]
    return _csv_response("inventory.csv", header, rows)

@router.get("/history.csv")
def export_history():
    rows = get_history(5000)
    header = ["id","tx_type","warehouse","location","item_code","lot_no","qty","remark","created_at"]
    return _csv_response("history.csv", header, rows)
