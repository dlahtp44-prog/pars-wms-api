from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["Inbound"])

@router.post("")
def inbound_item(
    item_code: str = Form(...),
    item_name: str = Form(...),
    brand: str = Form(...),
    spec: str = Form(...),
    location: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
):
    try:
        add_inventory(
            item_code=item_code,
            item_name=item_name,
            brand=brand,
            spec=spec,
            location=location,
            lot=lot,
            quantity=quantity
        )
        return {"result": "OK"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
