from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter(prefix="/worker")
templates = Jinja2Templates(directory="app/templates")

# 작업자 메인
@router.get("")
def worker_home(request: Request):
    return templates.TemplateResponse(
        "worker_home.html",
        {"request": request}
    )

# 입고
@router.get("/inbound")
def worker_inbound(request: Request):
    return templates.TemplateResponse(
        "worker_inbound.html",
        {"request": request}
    )

# 출고
@router.get("/outbound")
def worker_outbound(request: Request):
    return templates.TemplateResponse(
        "worker_outbound.html",
        {"request": request}
    )

# 재고 이동
@router.get("/move")
def worker_move(request: Request):
    return templates.TemplateResponse(
        "worker_move.html",
        {"request": request}
    )

# ✅ 재고 조회 (핵심 추가)
@router.get("/inventory")
def worker_inventory(request: Request):
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            location_name,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            location,
            qty
        FROM inventory
        ORDER BY item_code
    """).fetchall()
    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "rows": rows,
            "title": "작업자 재고 조회"
        }
    )
