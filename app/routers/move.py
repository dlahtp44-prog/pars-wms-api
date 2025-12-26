# app/routers/move.py
# =====================================
# MOVE API - FINAL
# =====================================

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from app.db import move_inventory, add_history, get_inventory

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
            from_loc=from_location,
            to_loc=to_location,
            lot=lot,
            quantity=quantity
        )

        add_history(
            action="MOVE",
            item_code=item_code,
            loc_from=from_location,
            loc_to=to_location,
            lot=lot,
            quantity=quantity
        )

        return {"result": "OK"}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
