from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
import urllib.parse

router = APIRouter(prefix="/label")
templates = Jinja2Templates(directory="app/templates")

@router.get("/product")
def product_label(
    request: Request,
    item_code: str,
    lot_no: str,
    item_name: str = "",
    spec: str = "",
    brand: str = ""
):
    qr = urllib.parse.urlencode({
        "item_code": item_code,
        "lot_no": lot_no,
        "item_name": item_name,
        "spec": spec,
        "brand": brand
    })
    return templates.TemplateResponse(
        "label_product.html",
        {"request": request, "qr": qr}
    )

@router.get("/location")
def location_label(request: Request, location: str):
    qr = urllib.parse.urlencode({"location": location})
    return templates.TemplateResponse(
        "label_location.html",
        {"request": request, "qr": qr}
    )
