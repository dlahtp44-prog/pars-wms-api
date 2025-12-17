
from fastapi import APIRouter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import qrcode
import json
import os
from datetime import datetime

router = APIRouter(tags=["QR 라벨 PDF"])

OUTPUT_DIR = "app/static/labels"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@router.post(
    "/qr/label/pdf",
    summary="QR 라벨 PDF 생성 (70x40mm)",
    description="70×40mm 규격의 QR 라벨 PDF를 생성합니다."
)
def generate_qr_label_pdf(
    item: str,
    qty: int,
    location: str,
    lot: str,
    action: str = "IN"
):
    # QR 데이터 (스캔용 JSON)
    payload = {
        "type": action,
        "item": item,
        "qty": qty,
        "location": location,
        "lot": lot
    }

    qr_text = json.dumps(payload, ensure_ascii=False)

    filename = f"QR_{item}_{lot}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # 70x40mm PDF
    c = canvas.Canvas(filepath, pagesize=(70 * mm, 40 * mm))

    # QR 이미지 생성
    qr_img = qrcode.make(qr_text)
    qr_path = "temp_qr.png"
    qr_img.save(qr_path)

    # QR 배치
    c.drawImage(qr_path, 2 * mm, 8 * mm, 24 * mm, 24 * mm)

    # 텍스트
    c.setFont("Helvetica", 7)
    c.drawString(28 * mm, 30 * mm, f"ITEM: {item}")
    c.drawString(28 * mm, 24 * mm, f"LOT : {lot}")
    c.drawString(28 * mm, 18 * mm, f"LOC : {location}")
    c.drawString(28 * mm, 12 * mm, f"QTY : {qty}")

    c.save()

    # 임시 QR 이미지 삭제
    if os.path.exists(qr_path):
        os.remove(qr_path)

    return {
        "결과": "QR 라벨 PDF 생성 완료",
        "파일": f"/static/labels/{filename}"
    }
