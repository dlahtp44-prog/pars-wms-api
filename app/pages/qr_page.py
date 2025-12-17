from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.utils.qr_image import generate_qr_image

router = APIRouter(prefix="/qr", tags=["QR"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/label")
def qr_label(
    request: Request,
    item_code: str,
    warehouse: str,
    location: str,
    lot_no: str,
    qty: int
):
    qr_url = generate_qr_image(item_code, warehouse, location, lot_no, qty)

    return templates.TemplateResponse("label.html", {
        "request": request,
        "qr_url": qr_url,
        "item_code": item_code,
        "warehouse": warehouse,
        "location": location,
        "lot_no": lot_no,
        "qty": qty
    })

