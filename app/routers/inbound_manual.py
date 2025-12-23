# app/routers/inbound_manual.py

from fastapi import APIRouter, Query, HTTPException
from app.db import add_inventory, log_history

router = APIRouter(
    prefix="/api/inbound",
    tags=["Inbound Manual"]
)

@router.get("/manual")
def inbound_manual(
    item_code: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    lot_no: str = Query(""),
    location: str = Query(...),
    qty: float = Query(..., gt=0),
    warehouse: str = Query("MAIN"),
    brand: str = Query("")
):
    """
    ✅ 수동 / QR 입고 처리 (QueryString 방식)
    예:
    /api/inbound/manual?item_code=728750&lot_no=H5415&location=D01-01&qty=10
    """

    try:
        # 1️⃣ 재고 증가
        add_inventory(
            warehouse=warehouse,
            location=location,
            brand=brand,
            item_code=item_code,
            item_name=item_name,
            lot_no=lot_no,
            spec=spec,
            qty=qty
        )

        # 2️⃣ 이력 기록
        log_history(
            tx_type="IN",
            warehouse=warehouse,
            location=location,
            item_code=item_code,
            lot_no=lot_no,
            qty=qty,
            remark="수동/QR 입고"
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "result": "OK",
        "msg": "입고 처리 완료",
        "warehouse": warehouse,
        "location": location,
        "item_code": item_code,
        "lot_no": lot_no,
        "qty": qty
    }
