from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/label")
templates = Jinja2Templates(directory="app/templates")

@router.get("/product")
def label_product(
    request: Request,
    item_code: str = Query(...),
    lot_no: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    brand: str = Query(""),
):
    # 제품 QR 내용: 제품라벨은 “품번/LOT 중심” + (선택) 상세
    qr = f"type=PRODUCT&item_code={item_code}&lot_no={lot_no}"
    return templates.TemplateResponse("label_product.html", {
        "request": request,
        "qr": qr,
        "item_code": item_code,
        "lot_no": lot_no,
        "item_name": item_name,
        "spec": spec,
        "brand": brand
    })

@router.get("/location")
def label_location(request: Request, location: str = Query(...), warehouse: str = Query("MAIN")):
    # 로케이션 QR은 스캔하면 해당 위치 재고 리스트로 이동
    qr = f"type=LOCATION&warehouse={warehouse}&location={location}"
    return templates.TemplateResponse("label_location.html", {
        "request": request,
        "qr": qr,
        "location": location,
        "warehouse": warehouse
    })
