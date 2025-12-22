from fastapi import APIRouter
from app.db import get_inventory, dashboard_summary

router = APIRouter(prefix="/api", tags=["재고"])

@router.get("/inventory")
def api_inventory(q: str | None = None, warehouse: str | None = None, location: str | None = None):
    return get_inventory(warehouse=warehouse, location=location, q=q)

@router.get("/dashboard")
def api_dashboard():
    return dashboard_summary()
