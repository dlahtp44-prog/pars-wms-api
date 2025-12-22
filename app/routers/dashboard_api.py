from fastapi import APIRouter
from app.db import dashboard_summary, dashboard_trend

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary")
def summary():
    return dashboard_summary()

@router.get("/trend")
def trend():
    return dashboard_trend(7)
