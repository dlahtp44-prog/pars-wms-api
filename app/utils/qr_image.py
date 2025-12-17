import qrcode
import os

def generate_qr_image(item_code, warehouse, location, lot_no, qty):
    qr_text = f"ITEM={item_code};WH={warehouse};LOC={location};LOT={lot_no};QTY={qty}"

    output_dir = "app/static/qr"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"qr_{item_code}_{lot_no}.png"
    output_path = os.path.join(output_dir, filename)

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

    return f"/static/qr/{filename}"

