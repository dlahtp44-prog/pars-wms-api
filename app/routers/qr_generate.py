from fastapi import APIRouter
import qrcode
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/qr", tags=["QR Generate"])

@router.get("/item")
def qr_item(item_code: str, lot_no: str, location: str, qty: float):
    data = (
        f"item_code={item_code}"
        f"&lot_no={lot_no}"
        f"&location={location}"
        f"&qty={qty}"
    )
    img = qrcode.make(data)
    path = "/tmp/item_qr.png"
    img.save(path)
    return FileResponse(path, filename="item_qr.png")

@router.get("/location")
def qr_location(location: str):
    img = qrcode.make(f"location={location}")
    path = "/tmp/location_qr.png"
    img.save(path)
    return FileResponse(path, filename="location_qr.png")
