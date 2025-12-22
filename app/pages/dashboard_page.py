from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory, dashboard_summary

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def dashboard(request: Request):
    rows = get_inventory()
    inbound, outbound, total, negative = dashboard_summary()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "rows": rows,
            "inbound": inbound,
            "outbound": outbound,
            "total": total,
            "negative": negative
        }
    )

# =========================
# 대시보드 요약
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고
    cur.execute("""
        SELECT IFNULL(SUM(qty), 0)
        FROM history
        WHERE tx_type = 'IN'
          AND date(created_at) = date('now')
    """)
    inbound_today = cur.fetchone()[0]

    # 오늘 출고
    cur.execute("""
        SELECT IFNULL(SUM(qty), 0)
        FROM history
        WHERE tx_type = 'OUT'
          AND date(created_at) = date('now')
    """)
    outbound_today = cur.fetchone()[0]

    # 총 재고
    cur.execute("""
        SELECT IFNULL(SUM(qty), 0)
        FROM inventory
    """)
    total_stock = cur.fetchone()[0]

    # 음수 재고
    cur.execute("""
        SELECT COUNT(*)
        FROM inventory
        WHERE qty < 0
    """)
    negative_stock = cur.fetchone()[0]

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative_stock
    }

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
