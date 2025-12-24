from fastapi import APIRouter
from app.db import get_inventory_by_location

router = APIRouter(prefix="/api/qr")

@router.post("/process")
def process_qr(data: dict):
    # 로케이션 QR 예시:
    # location=D01-01
    if "location" in data:
        return {
            "type": "LOCATION",
            "location": data["location"],
            "items": get_inventory_by_location(data["location"])
        }

    return {"error": "알 수 없는 QR"}
