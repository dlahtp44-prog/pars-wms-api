from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/label")
def label_page(request: Request):
    return templates.TemplateResponse(
        "label_print.html",
        {"request": request}
    )
