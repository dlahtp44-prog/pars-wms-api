from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from app.db import get_history, rollback
from app.auth import require_role

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

@router.get("")
def admin(request: Request, _:None=Depends(require_role("admin"))):
    rows = get_history()
    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "rows": rows}
    )

@router.post("/rollback/{tx_id}")
def do_rollback(tx_id: int, _:None=Depends(require_role("admin"))):
    rollback(tx_id)
    return {"ok": True}
