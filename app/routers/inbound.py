# app/routers/inbound.py
# =====================================
# INBOUND API - FINAL
# =====================================

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from app.db import add_inventory, add_history

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])


@router.post("")
def inbound_item(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(...),
    spec: str = Form(...),
    location_code: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
):
    try:
        # 재고 반영
        add_inventory(
            item_code=item_code,
            item_name=item_name,
            brand=brand,
            spec=spec,
            location_code=location_code,
            lot=lot,
            quantity=quantity
        )

        # 이력 기록
        add_history(
            action="INBOUND",
            item_code=item_code,
            loc_from="",
            loc_to=location_code,
            lot=lot,
            quantity=quantity
        )

        return {"result": "OK"}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
