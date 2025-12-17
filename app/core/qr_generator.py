import qrcode
import os
from datetime import datetime

def generate_qr_label(item_code, warehouse, location, lot_no, qty):
    """
    Railway 안전 버전
    - PDF ❌
    - QR 이미지(PNG)만 생성
    """

    # QR 텍스트 (기존 포맷 유지)
    qr_text = f"ITEM={item_code};WH={warehouse};LOC={location};LOT={lot_no};QTY={qty}"

    # 파일명
    filename = f"qr_{item_code}_{lot_no}.png"
    output_dir = "app/static/qr"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, filename)

    # QR 생성
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)

    return output_path

