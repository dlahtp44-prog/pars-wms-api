from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["Move"])

@router.post("")
def move_item(
    item_code: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    lot: str = Form(...),
    quantity: int = Form(...)
):
    try:
        move_inventory(
            item_code=item_code,
            from_location=from_location,
            to_location=to_location,
            lot=lot,
            quantity=quantity
        )
        return {"result": "OK"}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
