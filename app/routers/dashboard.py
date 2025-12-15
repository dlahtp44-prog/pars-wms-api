from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def dashboard_summary():
    return {"status": "DASHBOARD API OK"}
