from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_unchecked_qr_error_count

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "qr_error_cnt": get_unchecked_qr_error_count()
        }
    )
