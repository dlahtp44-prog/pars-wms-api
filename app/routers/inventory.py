from fastapi import APIRouter
from app.db import get_inventory

router = APIRouter(prefix="/api", tags=["재고"])

@router.get("/inventory")
def api_inventory(warehouse: str = "", location: str = "", q: str = ""):
    return get_inventory(warehouse=warehouse, location=location, q=q)
