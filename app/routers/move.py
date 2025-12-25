from fastapi import APIRouter, Form, HTTPException
from app.db import move_inventory

router = APIRouter(prefix="/api/move", tags=["Move"])

@router.post("/manual")
def move_manual(
    warehouse: str = Form(...),
    item_code: str = Form(...),
    from_location: str = Form(...),
    to_location: str = Form(...),
    qty: float = Form(...)
):
    try:
        ok = move_inventory(
            warehouse=warehouse,
            item_code=item_code,
            from_location=from_location,
            to_location=to_location,
            qty=qty
        )
        if not ok:
            raise HTTPException(status_code=400, detail="이동 실패")
        return {"result": "OK"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
