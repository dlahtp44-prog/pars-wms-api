# app/routers/qr_api.py
from fastapi import APIRouter, Query
from app.db import get_location_items, get_inventory

router = APIRouter(prefix="/api", tags=["QR API"])

@router.get("/location-items")
def api_location_items(warehouse: str = Query("MAIN"), location: str = Query(...)):
    return get_location_items(warehouse, location)

@router.get("/inventory")
def api_inventory(q: str = Query("")):
    return get_inventory(q)
