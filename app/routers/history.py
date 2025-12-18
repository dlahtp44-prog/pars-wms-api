from fastapi import APIRouter
from app.db import get_history

router = APIRouter(
    prefix="/api/history",
    tags=["작업이력"]
)

@router.get("/")
def history_api():
    rows = get_history()

    return [
        {
            "type": r["tx_type"],
            "item_code": r["item_code"],
            "qty": r["qty"],
            "location": r["location"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
