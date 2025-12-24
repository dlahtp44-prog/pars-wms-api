from fastapi import APIRouter, Query
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory")

@router.get("")
def inventory(q: str = Query("")):
    return get_inventory(q=q)
