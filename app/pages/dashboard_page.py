# app/pages/dashboard_page.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard(request: Request):
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='입고'
        AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = cur.fetchone()[0]

    # 오늘 출고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='출고'
        AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = cur.fetchone()[0]

    # 총 재고
    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = cur.fetchone()[0]

    # 위치 미지정
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM inventory
        WHERE location IS NULL OR location=''
    """)
    no_location = cur.fetchone()[0]

    conn.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "inbound_today": inbound_today,
            "outbound_today": outbound_today,
            "total_stock": total_stock,
            "no_location": no_location
        }
    )
