from fastapi import APIRouter
from app.db import get_inventory, dashboard_summary

router = APIRouter(prefix="/api", tags=["재고"])

@router.get("/inventory")
def inventory_api(q: str = "", warehouse: str = "", location: str = ""):
    rows = get_inventory(
        warehouse=warehouse if warehouse else None,
        location=location if location else None,
        q=q
    )
    return rows

@router.get("/dashboard")
def dashboard_api():
    return dashboard_summary()
