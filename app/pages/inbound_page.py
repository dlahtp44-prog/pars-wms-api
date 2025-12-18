from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/inbound-page")
def inbound_page(request: Request):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory")
    rows = [dict(zip(
        ["location_name","brand","item","name","lot","spec","location","qty"], r
    )) for r in cur.fetchall()]
    conn.close()

    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "rows": rows, "title": "입고 조회"}
    )
