from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/label")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def label_home(request: Request):
    # /label?mode=item 또는 /label?mode=location
    # 템플릿에서 모두 처리
    return templates.TemplateResponse("label_page.html", {"request": request})
