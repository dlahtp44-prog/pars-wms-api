from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/label")
templates = Jinja2Templates(directory="app/templates")

@router.get("/product-3108")
def product(request: Request, item_code: str, lot_no: str, item_name: str = "", spec: str = "", brand: str = ""):
    return templates.TemplateResponse("label_product_3108.html", {
        "request": request,
        "item_code": item_code, "lot_no": lot_no, "item_name": item_name, "spec": spec, "brand": brand
    })

@router.get("/location-3118")
def location(request: Request, warehouse: str = "MAIN", location: str = ""):
    return templates.TemplateResponse("label_location_3118.html", {
        "request": request,
        "warehouse": warehouse, "location": location
    })
