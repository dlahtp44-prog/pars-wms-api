from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/inbound-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def inbound_page(request: Request):
    return templates.TemplateResponse("worker_inbound.html", {"request": request})
