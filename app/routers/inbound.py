from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])


@router.post("")
def inbound_item(
    item_code: str = Form(...),
    location_code: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
):
    try:
        add_inventory(
            item_code=item_code,
            location_code=location_code,
            lot=lot,
            quantity=quantity
        )
        return {"result": "OK"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
