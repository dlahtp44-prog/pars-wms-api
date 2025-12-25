
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn
from datetime import date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/report/a3")
def report_a3(request: Request):
    conn = get_conn()
    cur = conn.cursor()

    # 전체 재고
    cur.execute("""
        SELECT warehouse, location, item_code, item_name, lot_no, spec, qty
        FROM inventory
        ORDER BY location, item_code
    """)
    inventory = cur.fetchall()

    # 위치별 합계
    cur.execute("""
        SELECT location, SUM(qty)
        FROM inventory
        GROUP BY location
        ORDER BY location
    """)
    location_summary = cur.fetchall()

    conn.close()

    return templates.TemplateResponse(
        "report_a3.html",
        {
            "request": request,
            "today": date.today().isoformat(),
            "inventory": inventory,
            "location_summary": location_summary
        }
    )
