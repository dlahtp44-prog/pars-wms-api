from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/worker")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def worker_home(request: Request):
    return templates.TemplateResponse("worker_home.html", {"request": request})

@router.get("/inbound")
def worker_inbound(request: Request):
    return templates.TemplateResponse("worker_inbound.html", {"request": request})

@router.get("/outbound")
def worker_outbound(request: Request):
    return templates.TemplateResponse("worker_outbound.html", {"request": request})

@router.get("/move")
def worker_move(request: Request):
    return templates.TemplateResponse("worker_move.html", {"request": request})

@router.get("/inventory")
def worker_inventory_redirect(request: Request):
    # 동일 템플릿을 inventory-page에서 제공하니 링크만 inventory-page로 두는 걸 권장
    return templates.TemplateResponse("inventory_page.html", {"request": request})
