from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

router = APIRouter(prefix="/api/qr", tags=["QR 생성"])

try:
    import qrcode
except ImportError:
    qrcode = None


@router.get("/product")
def product_qr(
    item_code: str,
    lot_no: str,
    item_name: str = "",
    spec: str = "",
    brand: str = ""
):
    if not qrcode:
        raise HTTPException(500, "qrcode 라이브러리 미설치")

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
    if not qrcode:
        raise HTTPException(500, "qrcode 라이브러리 미설치")

    data = f"location={location}&warehouse={warehouse}"

    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")
