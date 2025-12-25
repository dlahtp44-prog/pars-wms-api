from fastapi import APIRouter, Request
from app.db import move_inventory

router = APIRouter(prefix="/api/qr", tags=["QR"])

@router.post("/process")
async def qr_process(request: Request):
    data = await request.json()
    session = request.session

    qr_type = data.get("type")

    # 1️⃣ 출발 로케이션 스캔
    if qr_type == "LOC" and "move_from" not in session:
        session["move_from"] = data["location"]
        return {"step": 1, "msg": f"출발 위치 설정: {data['location']}"}

    # 2️⃣ 상품 스캔
    if qr_type == "ITEM" and "move_from" in session and "item" not in session:
        session["item"] = {
            "item_code": data["item_code"],
            "lot_no": data.get("lot_no", ""),
            "qty": data.get("qty", 1)
        }
        return {"step": 2, "msg": "상품 선택 완료. 목적지 스캔하세요"}

    # 3️⃣ 목적지 로케이션 스캔 → 이동 실행
    if qr_type == "LOC" and "move_from" in session and "item" in session:
        from_loc = session["move_from"]
        to_loc = data["location"]
        item = session["item"]

        move_inventory(
            warehouse="MAIN",
            item_code=item["item_code"],
            lot_no=item["lot_no"],
            qty=item["qty"],
            from_location=from_loc,
            to_location=to_loc
        )

        session.clear()

        return {
            "step": 3,
            "msg": f"이동 완료: {from_loc} → {to_loc}"
        }

    return {"error": "잘못된 QR 순서입니다"}
