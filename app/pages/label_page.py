# app/pages/label_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/labels")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def labels(request: Request):
    return templates.TemplateResponse("labels.html", {"request": request})
