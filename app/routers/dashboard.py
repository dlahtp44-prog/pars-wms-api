from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
def dashboard_summary():
    return {"status": "DASHBOARD API OK"}

            result["outbound_today"] = cursor.fetchone()[0] or 0
        except sqlite3.Error:
            pass

        # --------------------------------------------------
        # 총 재고 수량
        # --------------------------------------------------
        try:
            cursor.execute("""
                SELECT SUM(quantity)
                FROM inventory
            """)
            result["total_stock"] = cursor.fetchone()[0] or 0
        except sqlite3.Error:
            pass

        # --------------------------------------------------
        # 위치 미지정 재고
        # --------------------------------------------------
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM inventory
                WHERE location IS NULL OR location = ''
            """)
            result["no_location"] = cursor.fetchone()[0] or 0
        except sqlite3.Error:
            pass

    except Exception:
        # DB 자체 연결 실패해도 API는 응답
        pass

    return result
