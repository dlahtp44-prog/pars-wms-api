from fastapi import APIRouter, Query
from app.db import get_inventory

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("")
def inventory(
    item_code: str | None = Query(None),
    location_code: str | None = Query(None),
    lot: str | None = Query(None)
):
    """
    재고 조회
    - item_code
    - location_code
    - lot
    """
    return get_inventory(
        item_code=item_code,
        location_code=location_code,
        lot=lot
    )
