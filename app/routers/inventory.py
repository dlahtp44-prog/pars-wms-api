from fastapi import APIRouter
from app.db import get_inventory, get_location_items

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("")
def inventory_list():
    return get_inventory()


@router.get("/location/{location_code}")
def inventory_by_location(location_code: str):
    return get_location_items(location_code)
