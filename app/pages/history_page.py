from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/history-page")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def page(request: Request):
    # history_page.html을 띄워줍니다.
    return templates.TemplateResponse("history_page.html", {"request": request})
