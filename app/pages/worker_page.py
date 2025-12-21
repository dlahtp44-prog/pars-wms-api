from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_unchecked_qr_error_count

router = APIRouter(prefix="/worker")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def worker_home(request: Request):
    return templates.TemplateResponse(
        "worker_home.html",
        {
            "request": request,
            "qr_error_cnt": get_unchecked_qr_error_count()
        }
    )


@router.get("/inbound")
def worker_inbound(request: Request):
    return templates.TemplateResponse(
        "worker_inbound.html",
        {"request": request}
    )

@router.get("/outbound")
def worker_outbound(request: Request):
    return templates.TemplateResponse(
        "worker_outbound.html",
        {"request": request}
    )

@router.get("/move")
def worker_move(request: Request):
    return templates.TemplateResponse(
        "worker_move.html",
        {"request": request}
    )
@router.get("/qr")
def worker_qr(request: Request):
    return templates.TemplateResponse(
        "worker_qr.html",
        {"request": request}
    )

