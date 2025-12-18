from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_conn

router = APIRouter(
    prefix="/item",
    tags=["Item Page"]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/{item_code}")
def item_detail(request: Request, item_code: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            warehouse,      -- 장소명
            brand,          -- 브랜드
            item_code,      -- 품번
            item_name,      -- 품명
            lot_no,         -- LOT
            spec,           -- 규격
            location,       -- 로케이션
            qty             -- 현재고
        FROM inventory
        WHERE item_code = ?
    """, (item_code,))

    rows = cur.fetchall()
    conn.close()

    return templates.TemplateResponse(
        "item.html",
        {
            "request": request,
            "item_code": item_code,
            "rows": rows
        }
    )
