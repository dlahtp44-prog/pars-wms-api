
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from app.db import get_qr_errors

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/pages -> app
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/qr-errors", response_class=HTMLResponse)
def qr_errors_page(request: Request):
    rows = get_qr_errors(200)
    return templates.TemplateResponse(
        "admin_qr_errors.html",
        {"request": request, "rows": rows}
    )
