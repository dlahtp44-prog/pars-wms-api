# app/pages/upload_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/upload")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})
