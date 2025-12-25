from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import subtract_inventory

router = APIRouter(prefix="/api/outbound", tags=["Outbound"])


@router.post("")
def outbound_item(
    item_code: str = Form(...),
    location_code: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
):
    try:
        subtract_inventory(
            item_code=item_code,
            location_code=location_code,
            lot=lot,
            quantity=quantity
        )
        return {"result": "OK"}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
