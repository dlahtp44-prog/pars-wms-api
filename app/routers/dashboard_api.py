from fastapi import APIRouter
from app.db import get_conn
from datetime import date, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary")
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=6)).isoformat()

    # 오늘 입고
    cur.execute("""
        SELECT COALESCE(SUM(qty),0)
        FROM history
        WHERE tx_type='IN' AND DATE(created_at)=?
    """, (today,))
    inbound = cur.fetchone()[0]

    # 오늘 출고
    cur.execute("""
        SELECT COALESCE(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT' AND DATE(created_at)=?
    """, (today,))
    outbound = cur.fetchone()[0]

    # 재고 TOP 5
    cur.execute("""
        SELECT item_code, SUM(qty) AS total
        FROM inventory
        GROUP BY item_code
        ORDER BY total DESC
        LIMIT 5
    """)
    top_items = cur.fetchall()

    # 최근 7일 입출고
    cur.execute("""
        SELECT DATE(created_at) d,
               SUM(CASE WHEN tx_type='IN' THEN qty ELSE 0 END) in_qty,
               SUM(CASE WHEN tx_type='OUT' THEN qty ELSE 0 END) out_qty
        FROM history
        WHERE DATE(created_at)>=?
        GROUP BY DATE(created_at)
        ORDER BY d
    """, (week_ago,))
    weekly = cur.fetchall()

    conn.close()

    return {
        "today": {
            "in": inbound,
            "out": outbound
        },
        "top_items": [
            {"item_code": r[0], "qty": r[1]} for r in top_items
        ],
        "weekly": [
            {"date": r[0], "in": r[1], "out": r[2]} for r in weekly
        ]
    }
