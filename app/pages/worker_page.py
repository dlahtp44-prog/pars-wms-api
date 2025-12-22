# app/pages/worker_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/worker")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def worker_home(request: Request):
    return templates.TemplateResponse(
        "worker_home.html",
        {"request": request}
    )

@router.get("/inbound")
def inbound(request: Request):
    return templates.TemplateResponse("worker_inbound.html", {"request": request})

@router.get("/outbound")
def outbound(request: Request):
    return templates.TemplateResponse("worker_outbound.html", {"request": request})

@router.get("/move")
def move(request: Request):
    return templates.TemplateResponse("worker_move.html", {"request": request})

@router.get("/inventory")
def inventory(request: Request):
    return templates.TemplateResponse("inventory.html", {"request": request})
