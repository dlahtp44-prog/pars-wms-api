from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.db import add_inventory

router = APIRouter(prefix="/api/inbound", tags=["입고"])

class InboundBody(BaseModel):
    warehouse: str = "MAIN"
    location: str
    brand: str = ""
    item_code: str
    item_name: str = ""
    lot_no: str
    spec: str = ""
    qty: float

@router.get("/manual")
def inbound_manual_get(
    item_code: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    lot_no: str = Query(...),
    location: str = Query(...),
    qty: float = Query(...),
    warehouse: str = Query("MAIN"),
    brand: str = Query(""),
):
    add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark="QR/GET 입고")
    return {"result": "OK", "msg": "입고 완료(GET)", "item_code": item_code, "lot_no": lot_no, "qty": qty}

@router.post("/manual")
def inbound_manual_post(body: InboundBody):
    add_inventory(
        body.warehouse, body.location, body.brand,
        body.item_code, body.item_name, body.lot_no, body.spec, body.qty,
        remark="수동/POST 입고"
    )
    return {"result": "OK", "msg": "입고 완료(POST)"}
