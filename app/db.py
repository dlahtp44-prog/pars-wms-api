# =========================
# 대시보드 요약
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type IN ('IN','입고')
          AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = cur.fetchone()[0]

    # 오늘 출고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type IN ('OUT','출고')
          AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = cur.fetchone()[0]

    # 총 재고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM inventory
    """)
    total_stock = cur.fetchone()[0]

    # 음수 재고
    cur.execute("""
        SELECT COUNT(*)
        FROM inventory
        WHERE qty < 0
    """)
    negative_stock = cur.fetchone()[0]

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative_stock
    }
