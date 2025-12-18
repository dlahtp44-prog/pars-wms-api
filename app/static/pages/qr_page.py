from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/qr-page")
def qr_page(
    request: Request,
    item: str | None = Query(None)
):
    rows = []
    if item:
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM inventory WHERE item_code=?",
            (item,)
        ).fetchall()
        conn.close()

    return templates.TemplateResponse(
        "qr.html",
        {"request": request, "rows": rows}
    )
