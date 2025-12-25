from fastapi import APIRouter, Request
from app.db import move_inventory

router = APIRouter(prefix="/api/qr")

@router.post("/process")
def qr_process(req: Request, body: dict):
    session = req.session
    action = body.get("action")

    if action == "MOVE":
        # 1️⃣ 출발 로케이션
        if "location" in body and "from_location" not in session:
            session["from_location"] = body["location"]
            return {"step": 1, "msg": "출발 위치 저장"}

        # 2️⃣ 제품 선택
        if "item_code" in body:
            session["item"] = body
            return {"step": 2, "msg": "제품 선택 완료"}

        # 3️⃣ 목적지
        if "location" in body and "item" in session:
            item = session["item"]
            move_inventory(
                "MAIN",
                session["from_location"],
                body["location"],
                item["item_code"],
                item["lot_no"],
                item["qty"]
            )
            session.clear()
            return {"step": 3, "msg": "이동 완료"}

    return {"error": "처리 불가"}
