from fastapi import APIRouter
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import qrcode
import os
import json

router = APIRouter(prefix="/api", tags=["QR-LABEL"])

OUTPUT_DIR = "app/static/labels"
os.makedirs(OUTPUT_DIR, exist_ok=True)

LABEL_W = 50 * mm
LABEL_H = 30 * mm

@router.post("/qr/label")
def create_qr_label(data: dict):
    """
    data = {
      location_name, brand, item_code, lot_no,
      spec, location, type, qty
    }
    """

    filename = f"qr_{data['item_code']}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    c = canvas.Canvas(filepath, pagesize=A4)

    x, y = 10 * mm, A4[1] - 40 * mm

    qr_payload = json.dumps({
        "type": data["type"],
        "item_code": data["item_code"],
        "qty": data["qty"],
        "to_location": data["location"]
    }, ensure_ascii=False)

    qr_img = qrcode.make(qr_payload)
    qr_path = os.path.join(OUTPUT_DIR, "tmp_qr.png")
    qr_img.save(qr_path)

    c.drawImage(qr_path, x, y, 20*mm, 20*mm)

    text_x = x + 22*mm
    text_y = y + 15*mm

    c.setFont("Helvetica", 7)
    c.drawString(text_x, text_y, f"장소: {data['location_name']}")
    c.drawString(text_x, text_y-8, f"브랜드: {data['brand']}")
    c.drawString(text_x, text_y-16, f"품번: {data['item_code']}")
    c.drawString(text_x, text_y-24, f"LOT: {data['lot_no']}")
    c.drawString(text_x, text_y-32, f"규격: {data['spec']}")
    c.drawString(text_x, text_y-40, f"LOC: {data['location']}")

    c.showPage()
    c.save()

    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=filename
    )

