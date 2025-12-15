from fastapi import APIRouter
from app.db import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def dashboard_summary():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM inbound WHERE date = DATE('now')")
    inbound_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM outbound WHERE date = DATE('now')")
    outbound_today = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity) FROM inventory")
    total_stock = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM inventory WHERE location IS NULL")
    no_location = cursor.fetchone()[0]

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "no_location": no_location
    }
