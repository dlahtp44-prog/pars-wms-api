# app/routers/inventory.py
# =====================================
# INVENTORY API - FINAL
# =====================================

from fastapi import APIRouter
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("")
def inventory():
    rows = get_inventory()

    result = []
    for r in rows:
        result.append({
            "item_code": r[0],
            "item_name": r[1],
            "brand": r[2],
            "spec": r[3],
            "location_code": r[4],
            "lot": r[5],
            "quantity": r[6]
        })

    return result
