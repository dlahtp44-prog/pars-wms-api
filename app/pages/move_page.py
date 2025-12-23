from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/move-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def move_page(request: Request):
    return templates.TemplateResponse("worker_move.html", {"request": request})
