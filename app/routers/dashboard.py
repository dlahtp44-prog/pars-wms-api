from fastapi import APIRouter
from app.db import get_db
import sqlite3

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard_summary():
    """
    대시보드 요약 API
    - DB 오류가 나도 절대 무한 로딩되지 않음
    - 테이블/컬럼이 없으면 0으로 처리
    """

    result = {
        "inbound_today": 0,
        "outbound_today": 0,
        "total_stock": 0,
        "no_location": 0
    }

    try:
        db = get_db()
        cursor = db.cursor()

        # --------------------------------------------------
        # 오늘 입고 건수
        # --------------------------------------------------
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM inbound
                WHERE DATE(created_at) = DATE('now')
            """)
            result["inbound_today"] = cursor.fetchone()[0] or 0
        except sqlite3.Error:
            pass   # 테이블/컬럼 없으면 0 유지

        # --------------------------------------------------
        # 오늘 출고 건수
        # --------------------------------------------------
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM outbound
                WHERE DATE(created_at) = DATE('now')
            """)
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
