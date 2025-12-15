from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def dashboard_summary():
    return {
        "inbound_today": 0,
        "outbound_today": 0,
        "total_stock": 0,
        "no_location": 0,
        "status": "DASHBOARD API OK"
    }
