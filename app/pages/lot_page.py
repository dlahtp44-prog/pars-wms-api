from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/lot-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request):
    return templates.TemplateResponse("lot.html", {"request": request})
