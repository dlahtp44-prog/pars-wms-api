from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/label")
templates = Jinja2Templates(directory="app/templates")

# HEQ-3108 제품 라벨 (품번/LOT/품명/규격/브랜드 + QR)
@router.get("/product")
def label_product(
    request: Request,
    item_code: str,
    lot_no: str,
    item_name: str = "",
    spec: str = "",
    brand: str = "",
):
    # QR에 넣을 문자열(querystring). (필드 확장 가능)
    qr = f"item_code={item_code}&lot_no={lot_no}"
    return templates.TemplateResponse("label_product.html", {
        "request": request,
        "item_code": item_code,
        "lot_no": lot_no,
        "item_name": item_name,
        "spec": spec,
        "brand": brand,
        "qr_text": qr
    })

# HEQ-3118 로케이션 라벨 (location + QR: /loc/{location})
@router.get("/location")
def label_location(request: Request, location: str, warehouse: str = "MAIN"):
    base = str(request.base_url).rstrip("/")
    qr_url = f"{base}/loc/{location}?warehouse={warehouse}"
    return templates.TemplateResponse("label_location.html", {
        "request": request,
        "location": location,
        "warehouse": warehouse,
        "qr_text": qr_url
    })
