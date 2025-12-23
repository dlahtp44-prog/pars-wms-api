from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import qrcode
import io

router = APIRouter(prefix="/api/qr", tags=["QR 생성"])

@router.get("/product")
def product_qr(
    item_code: str,
    lot_no: str,
    item_name: str = "",
    spec: str = "",
    brand: str = ""
):
    data = (
        f"item_code={item_code}"
        f"&lot_no={lot_no}"
        f"&item_name={item_name}"
        f"&spec={spec}"
        f"&brand={brand}"
    )

    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.get("/location")
def location_qr(location: str, warehouse: str = "MAIN"):
    data = f"location={location}&warehouse={warehouse}"

    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")
