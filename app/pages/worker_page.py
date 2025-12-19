from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/worker", tags=["Worker Pages"])
templates = Jinja2Templates(directory="app/templates")


# =========================
# 작업자 메인
# =========================
@router.get("")
def worker_home(request: Request):
    return templates.TemplateResponse(
        "worker_home.html",
        {"request": request}
    )


# =========================
# 작업자 입고
# =========================
@router.get("/inbound")
def worker_inbound(request: Request):
    return templates.TemplateResponse(
        "worker_inbound.html",
        {"request": request}
    )


# =========================
# 작업자 출고
# =========================
@router.get("/outbound")
def worker_outbound(request: Request):
    return templates.TemplateResponse(
        "worker_outbound.html",
        {"request": request}
    )


# =========================
# 작업자 재고 이동
# =========================
@router.get("/move")
def worker_move(request: Request):
    return templates.TemplateResponse(
        "worker_move.html",
        {"request": request}
    )


# =========================
# 작업자 QR 스캔
# =========================
@router.get("/qr")
def worker_qr(request: Request):
    return templates.TemplateResponse(
        "qr.html",
        {"request": request}
    )
