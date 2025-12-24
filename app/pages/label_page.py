# app/pages/label_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/label")
templates = Jinja2Templates(directory="app/templates")

@router.get("/product")
def product(request: Request,
            item_code: str,
            lot_no: str,
            item_name: str = "",
            spec: str = "",
            brand: str = ""):
    # 제품 QR 내용: 제품 조회/출고/이동에 쓰기 쉬운 querystring 형태
    qr = f"item_code={item_code}&lot_no={lot_no}&item_name={item_name}&spec={spec}&brand={brand}"
    return templates.TemplateResponse(
        "label_product.html",
        {"request": request, "qr": qr, "item_code": item_code, "lot_no": lot_no,
         "item_name": item_name, "spec": spec, "brand": brand}
    )

@router.get("/location")
def location(request: Request, loc: str):
    # 로케이션 QR: 스캔하면 해당 위치 재고 페이지로 바로 연결
    # (QR카메라에서 URL이면 그대로 열거나, 텍스트면 파싱해서 loc로 처리하도록 해도 됨)
    qr = f"/loc/{loc}"
    return templates.TemplateResponse("label_location.html", {"request": request, "qr": qr, "loc": loc})
