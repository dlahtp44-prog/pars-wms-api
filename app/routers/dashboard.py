from fastapi import APIRouter
from app.db import dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("")
def dashboard():
    return dashboard_summary()
