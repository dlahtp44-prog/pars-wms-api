from fastapi import APIRouter, HTTPException
from app.db import add_inventory

router = APIRouter(prefix="/api/qr", tags=["QR"])

@router.post("")
def process_qr(data: dict):
    """
    QR 데이터 예시:
    {
      "warehouse":"A",
      "location":"A01-01",
      "item_code":"766109",
      "item_name":"Buildtech",
      "lot_no":"E465",
      "spec":"1200x2400",
      "qty":1,
      "tx_type":"OUT"
    }
    """

    try:
        add_inventory(
            tx_type=data.get("tx_type", "OUT"),
            warehouse=data["warehouse"],
            location=data["location"],
            item_code=data["item_code"],
            item_name=data.get("item_name", ""),
            lot_no=data.get("lot_no", ""),
            spec=data.get("spec", ""),
            qty=float(data.get("qty", 1)),
            remark="QR 스캔"
        )
        return {"ok": True}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
