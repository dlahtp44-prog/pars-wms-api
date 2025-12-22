from fastapi import APIRouter
from pydantic import BaseModel
from app.db import add_inventory

router = APIRouter(prefix="/api")

class QRBody(BaseModel):
    qr: str

@router.post("/qr")
def process_qr(body: QRBody):
    """
    QR 포맷 예시:
    W1|B01-01-02-A|ITEM001|LOT123|10|IN
    """
    try:
        parts = body.qr.split("|")
        if len(parts) != 6:
            return {"ok": False, "msg": "QR 형식 오류"}

        warehouse, location, item, lot, qty, tx = parts
        qty = float(qty)

        if tx == "OUT":
            qty = -qty

        add_inventory(
            warehouse=warehouse,
            location=location,
            item=item,
            lot=lot,
            qty=qty
        )

        return {"ok": True}

    except ValueError as e:
        return {"ok": False, "msg": str(e)}

    except Exception:
        return {"ok": False, "msg": "처리 실패"}
