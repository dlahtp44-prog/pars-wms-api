from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin")
def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )
