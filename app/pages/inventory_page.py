from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/inventory")
def inventory_page(request: Request):
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request}
    )
