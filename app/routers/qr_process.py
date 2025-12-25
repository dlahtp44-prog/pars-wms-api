# app/routers/qr_process.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.db import add_inventory, subtract_inventory, move_inventory

router = APIRouter(prefix="/api/qr", tags=["qr-process"])

class QRBody(BaseModel):
    action: str  # IN / OUT / MOVE / LOC / ITEM
    warehouse: str = "MAIN"
    location: str = ""
    from_location: str = ""
    to_location: str = ""
    brand: str = ""
    item_code: str = ""
    item_name: str = ""
    lot_no: str = ""
    spec: str = ""
    qty: float = 0

@router.post("/process")
def process(request: Request, body: QRBody):
    a = (body.action or "").upper()

    # 1) 로케이션 선스캔 (MOVE 준비)
    if a == "LOC":
        request.session["move_from"] = body.location
        request.session.pop("move_item", None)
        return {"ok": True, "mode": "MOVE_STEP1", "from": body.location}

    # 2) 제품 스캔(이동 대상 선택)
    if a == "ITEM":
        if not request.session.get("move_from"):
            return {"ok": False, "detail": "로케이션(LOC) 먼저 스캔하세요."}
        request.session["move_item"] = {
            "item_code": body.item_code,
            "item_name": body.item_name,
            "lot_no": body.lot_no,
            "spec": body.spec,
            "brand": body.brand,
            "qty": float(body.qty or 0)
        }
        return {"ok": True, "mode": "MOVE_STEP2", "picked": request.session["move_item"]}

    # 3) 목적지 로케이션 스캔하면 MOVE 실행
    if a == "MOVE":
        frm = request.session.get("move_from") or body.from_location
        item = request.session.get("move_item") or {}
        to = body.to_location or body.location
        qty = float(body.qty or item.get("qty") or 0)

        if not frm:
            return {"ok": False, "detail": "출발 로케이션이 없습니다. LOC 먼저 스캔하세요."}
        if not to:
            return {"ok": False, "detail": "목적지 로케이션이 없습니다."}
        if not item.get("item_code"):
            return {"ok": False, "detail": "이동할 제품이 선택되지 않았습니다. ITEM 스캔하세요."}
        if qty <= 0:
            return {"ok": False, "detail": "수량(qty)이 0입니다."}

        move_inventory(
            warehouse=body.warehouse,
            from_location=frm,
            to_location=to,
            brand=item.get("brand",""),
            item_code=item["item_code"],
            item_name=item.get("item_name",""),
            lot_no=item.get("lot_no",""),
            spec=item.get("spec",""),
            qty=qty,
            remark="QR 2단계 이동",
            block_negative=True
        )
        # 상태 초기화
        request.session.pop("move_from", None)
        request.session.pop("move_item", None)
        return {"ok": True, "moved": True, "from": frm, "to": to}

    # 기존 IN/OUT는 그대로 지원
    if a == "IN":
        add_inventory(body.warehouse, body.location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, body.qty, remark="QR 입고")
        return {"ok": True, "action": "IN"}

    if a == "OUT":
        subtract_inventory(body.warehouse, body.location, body.brand, body.item_code, body.item_name, body.lot_no, body.spec, body.qty, remark="QR 출고", block_negative=True)
        return {"ok": True, "action": "OUT"}

    return {"ok": False, "detail": "지원하지 않는 action"}
