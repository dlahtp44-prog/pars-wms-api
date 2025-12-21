from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/worker")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def worker_home(request: Request):
    return templates.TemplateResponse("worker_home.html", {"request": request})
