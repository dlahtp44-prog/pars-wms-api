from fastapi import APIRouter
import qrcode
import json
import os
from datetime import datetime

router = APIRouter(tags=["QR 라벨"])

OUTPUT_DIR = "app/static/labels"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@router.post(
    "/qr/label",
    summary="QR 라벨 생성",
    description="품목/수량/위치 정보를 담은 QR 라벨 이미지를 생성합니다."
)
def generate_qr_label(
    item: str,
    qty: int,
    location: str,
    lot: str,
    action: str = "IN"
):
    payload = {
        "type": action,
        "item": item,
        "qty": qty,
        "location": location,
        "lot": lot
    }

    qr_text = json.dumps(payload, ensure_ascii=False)

    filename = f"QR_{item}_{lot}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)

    img = qrcode.make(qr_text)
    img.save(filepath)

    return {
        "결과": "QR 라벨 생성 완료",
        "파일": f"/static/labels/{filename}",
        "QR데이터": payload
    }

