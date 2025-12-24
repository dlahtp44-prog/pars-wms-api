# app/db.py  (✅ A안 기준 · 전체 교체용 완성본)
import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# =========================
# DB 경로
# =========================
DB_PATH = Path(__file__).parent.parent / "WMS.db"


# =========================
# Connection
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# DB 초기화
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ---- locations (로케이션 이름 매핑)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        location_name TEXT DEFAULT '',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_locations
    ON locations(warehouse, location)
    """)

    # ---- inventory (재고: 창고/로케이션/품번/LOT 기준)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT NOT NULL,
        location TEXT NOT NULL,
        location_name TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL,
        spec TEXT DEFAULT '',
        qty REAL DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory(warehouse, location, item_code, lot_no)
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_inventory_item
    ON inventory(item_code)
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_inventory_location
    ON inventory(warehouse, location)
    """)

    # ---- history (작업 이력 + 롤백용 메타)
    # tx_type: IN / OUT / MOVE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT NOT NULL,
        warehouse TEXT NOT NULL,
        location TEXT DEFAULT '',          -- 보통 "대상 로케이션"(MOVE는 to_location)
        from_location TEXT DEFAULT '',     -- MOVE 롤백용
        to_location TEXT DEFAULT '',       -- MOVE 롤백용
        location_name TEXT DEFAULT '',
        item_code TEXT NOT NULL,
        item_name TEXT DEFAULT '',
        lot_no TEXT NOT NULL,
        spec TEXT DEFAULT '',
        brand TEXT DEFAULT '',
        qty REAL NOT NULL,
        remark TEXT DEFAULT '',
        is_rolled_back INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_history_created
    ON history(created_at)
    """)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS ix_history_item
    ON history(item_code, lot_no)
    """)

    conn.commit()
    conn.close()


# =========================
# 관리자 비밀번호 체크
# =========================
def admin_password_ok(pw: str) -> bool:
    # 환경변수로 운영 권장: ADMIN_PASSWORD
    # 로컬/테스트용 기본값
    admin_pw = os.getenv("ADMIN_PASSWORD", "1234")
    return (pw or "") == admin_pw


# =========================
# Location Upsert
# =========================
def upsert_location(warehouse: str, location: str, location_name: str = ""):
    warehouse = (warehouse or "").strip() or "MAIN"
    location = (location or "").strip()
    location_name = (location_name or "").strip()

    if not location:
        return  # 빈 로케이션은 저장 안 함

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO locations(warehouse, location, location_name, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location)
        DO UPDATE SET
            location_name=excluded.location_name,
            updated_at=CURRENT_TIMESTAMP
    """, (warehouse, location, location_name))
    conn.commit()
    conn.close()


def get_location_name(warehouse: str, location: str) -> str:
    warehouse = (warehouse or "").strip() or "MAIN"
    location = (location or "").strip()
    if not location:
        return ""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT location_name
        FROM locations
        WHERE warehouse=? AND location=?
    """, (warehouse, location))
    row = cur.fetchone()
    conn.close()
    return (row["location_name"] if row else "") or ""


# =========================
# History 기록
# =========================
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "",
    *,
    from_location: str = "",
    to_location: str = "",
    location_name: str = "",
    brand: str = "",
    item_name: str = "",
    spec: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location, location_name,
         item_code, item_name, lot_no, spec, brand, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type,
        warehouse,
        location,
        from_location,
        to_location,
        location_name,
        item_code,
        item_name,
        lot_no,
        spec,
        brand,
        float(qty),
        remark
    ))

    conn.commit()
    conn.close()


# =========================
# Inventory 공통 UPSERT
# =========================
def _upsert_inventory_row(
    cur,
    warehouse: str,
    location: str,
    location_name: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    delta_qty: float
):
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, location_name, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            location_name=excluded.location_name,
            brand=excluded.brand,
            item_name=excluded.item_name,
            spec=excluded.spec,
            qty = inventory.qty + excluded.qty,
            updated_at=CURRENT_TIMESTAMP
    """, (
        warehouse, location, location_name, brand,
        item_code, item_name, lot_no, spec,
        float(delta_qty)
    ))


# =========================
# ✅ 입고 (재고 증가)
# =========================
def add_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    *,
    location_name: str = "",
    remark: str = "입고"
):
    warehouse = (warehouse or "").strip() or "MAIN"
    location = (location or "").strip()
    item_code = (item_code or "").strip()
    lot_no = (lot_no or "").strip()
    item_name = (item_name or "").strip()
    brand = (brand or "").strip()
    spec = (spec or "").strip()
    qty = float(qty or 0)

    if not (location and item_code and lot_no):
        raise ValueError("warehouse/location/item_code/lot_no 필수")
    if qty == 0:
        raise ValueError("qty는 0이 될 수 없습니다")

    # location_name 자동 보강(입력 없으면 locations에서 가져오기)
    if not location_name:
        location_name = get_location_name(warehouse, location)
    else:
        upsert_location(warehouse, location, location_name)

    conn = get_conn()
    cur = conn.cursor()

    _upsert_inventory_row(
        cur, warehouse, location, location_name, brand,
        item_code, item_name, lot_no, spec,
        abs(qty)  # 입고는 +로 처리
    )

    conn.commit()
    conn.close()

    log_history(
        "IN",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=abs(qty),
        remark=remark,
        location_name=location_name,
        brand=brand,
        item_name=item_name,
        spec=spec
    )


# =========================
# ✅ 출고 (재고 차감)
# =========================
def subtract_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    *,
    location_name: str = "",
    remark: str = "출고",
    strict: bool = False
):
    """
    strict=True 이면 재고 부족 시 에러
    strict=False 이면 음수 허용(현장 상황 대응)
    """
    warehouse = (warehouse or "").strip() or "MAIN"
    location = (location or "").strip()
    item_code = (item_code or "").strip()
    lot_no = (lot_no or "").strip()
    item_name = (item_name or "").strip()
    brand = (brand or "").strip()
    spec = (spec or "").strip()
    qty = float(qty or 0)

    if not (location and item_code and lot_no):
        raise ValueError("warehouse/location/item_code/lot_no 필수")
    if qty == 0:
        raise ValueError("qty는 0이 될 수 없습니다")

    if not location_name:
        location_name = get_location_name(warehouse, location)
    else:
        upsert_location(warehouse, location, location_name)

    conn = get_conn()
    cur = conn.cursor()

    if strict:
        cur.execute("""
            SELECT IFNULL(qty,0) AS qty
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (warehouse, location, item_code, lot_no))
        row = cur.fetchone()
        now_qty = float(row["qty"]) if row else 0.0
        if now_qty < abs(qty):
            conn.close()
            raise ValueError("출고 재고 부족")

    _upsert_inventory_row(
        cur, warehouse, location, location_name, brand,
        item_code, item_name, lot_no, spec,
        -abs(qty)  # 출고는 -로 처리
    )

    conn.commit()
    conn.close()

    log_history(
        "OUT",
        warehouse=warehouse,
        location=location,
        item_code=item_code,
        lot_no=lot_no,
        qty=abs(qty),
        remark=remark,
        location_name=location_name,
        brand=brand,
        item_name=item_name,
        spec=spec
    )


# =========================
# ✅ 이동 (from -> to)
# =========================
def move_inventory(
    warehouse: str,
    from_location: str,
    to_location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    *,
    from_location_name: str = "",
    to_location_name: str = "",
    remark: str = "이동",
    strict: bool = False
):
    """
    strict=True: 출발지 재고 부족 시 에러
    """
    warehouse = (warehouse or "").strip() or "MAIN"
    from_location = (from_location or "").strip()
    to_location = (to_location or "").strip()
    item_code = (item_code or "").strip()
    lot_no = (lot_no or "").strip()
    item_name = (item_name or "").strip()
    brand = (brand or "").strip()
    spec = (spec or "").strip()
    qty = float(qty or 0)

    if not (from_location and to_location and item_code and lot_no):
        raise ValueError("warehouse/from_location/to_location/item_code/lot_no 필수")
    if qty == 0:
        raise ValueError("qty는 0이 될 수 없습니다")

    # 로케이션명 보강
    if not from_location_name:
        from_location_name = get_location_name(warehouse, from_location)
    else:
        upsert_location(warehouse, from_location, from_location_name)

    if not to_location_name:
        to_location_name = get_location_name(warehouse, to_location)
    else:
        upsert_location(warehouse, to_location, to_location_name)

    conn = get_conn()
    cur = conn.cursor()

    if strict:
        cur.execute("""
            SELECT IFNULL(qty,0) AS qty
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (warehouse, from_location, item_code, lot_no))
        row = cur.fetchone()
        now_qty = float(row["qty"]) if row else 0.0
        if now_qty < abs(qty):
            conn.close()
            raise ValueError("이동 재고 부족")

    # 출발지 차감
    _upsert_inventory_row(
        cur, warehouse, from_location, from_location_name, brand,
        item_code, item_name, lot_no, spec,
        -abs(qty)
    )
    # 도착지 증가
    _upsert_inventory_row(
        cur, warehouse, to_location, to_location_name, brand,
        item_code, item_name, lot_no, spec,
        abs(qty)
    )

    conn.commit()
    conn.close()

    # history: MOVE는 location=to_location 로 통일(화면 표시 편의)
    log_history(
        "MOVE",
        warehouse=warehouse,
        location=to_location,
        from_location=from_location,
        to_location=to_location,
        location_name=to_location_name,
        item_code=item_code,
        lot_no=lot_no,
        qty=abs(qty),
        remark=remark,
        brand=brand,
        item_name=item_name,
        spec=spec
    )


# =========================
# ✅ 재고 조회 (검색/필터)
# =========================
def get_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT
            warehouse,
            location,
            location_name,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            qty,
            updated_at
        FROM inventory
        WHERE 1=1
    """
    params: List[Any] = []

    if warehouse:
        sql += " AND warehouse = ?"
        params.append(warehouse)

    if location:
        sql += " AND location = ?"
        params.append(location)

    if q is not None:
        kw = f"%{q.strip()}%"
        sql += """
        AND (
            item_code LIKE ?
            OR item_name LIKE ?
            OR lot_no LIKE ?
            OR brand LIKE ?
            OR spec LIKE ?
            OR location LIKE ?
            OR location_name LIKE ?
        )
        """
        params.extend([kw, kw, kw, kw, kw, kw, kw])

    sql += " ORDER BY item_code, lot_no, location"

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# ✅ 이력 조회
# =========================
def get_history(limit: int = 200) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
    """, (int(limit),))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# ✅ 롤백 (관리자)
# =========================
def rollback(history_id: int) -> Dict[str, Any]:
    """
    history_id 기준으로 반대 작업 실행 후 is_rolled_back=1 처리
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (int(history_id),))
    h = cur.fetchone()
    if not h:
        conn.close()
        raise ValueError("해당 이력 없음")

    if int(h["is_rolled_back"]) == 1:
        conn.close()
        raise ValueError("이미 롤백된 이력")

    tx_type = h["tx_type"]
    warehouse = h["warehouse"]
    item_code = h["item_code"]
    lot_no = h["lot_no"]
    qty = float(h["qty"])
    brand = h["brand"] or ""
    item_name = h["item_name"] or ""
    spec = h["spec"] or ""

    # 롤백 실행은 같은 트랜잭션으로 처리
    try:
        if tx_type == "IN":
            # 입고 롤백 = 동일 키에서 수량 차감
            _upsert_inventory_row(
                cur,
                warehouse, h["location"], h["location_name"] or "",
                brand, item_code, item_name, lot_no, spec,
                -abs(qty)
            )

        elif tx_type == "OUT":
            # 출고 롤백 = 동일 키에서 수량 증가
            _upsert_inventory_row(
                cur,
                warehouse, h["location"], h["location_name"] or "",
                brand, item_code, item_name, lot_no, spec,
                abs(qty)
            )

        elif tx_type == "MOVE":
            # 이동 롤백 = to -> from
            from_loc = h["from_location"] or ""
            to_loc = h["to_location"] or h["location"] or ""
            if not (from_loc and to_loc):
                raise ValueError("MOVE 롤백 정보(from/to location) 부족")

            # to 차감
            _upsert_inventory_row(
                cur,
                warehouse, to_loc, get_location_name(warehouse, to_loc),
                brand, item_code, item_name, lot_no, spec,
                -abs(qty)
            )
            # from 증가
            _upsert_inventory_row(
                cur,
                warehouse, from_loc, get_location_name(warehouse, from_loc),
                brand, item_code, item_name, lot_no, spec,
                abs(qty)
            )

        else:
            raise ValueError("알 수 없는 tx_type")

        cur.execute("UPDATE history SET is_rolled_back=1 WHERE id=?", (int(history_id),))
        conn.commit()

    except Exception:
        conn.rollback()
        conn.close()
        raise

    conn.close()
    return {"result": "OK", "msg": f"rollback done: {history_id}"}


# =========================
# ✅ 대시보드 요약
# =========================
def dashboard_summary() -> Dict[str, Any]:
    """
    페이지/ API 공통으로 쓰기 좋게 dict 반환
    """
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고/출고 (localtime)
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM history
        WHERE tx_type='IN'
          AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = float(cur.fetchone()["v"])

    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM history
        WHERE tx_type='OUT'
          AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = float(cur.fetchone()["v"])

    # 총 재고
    cur.execute("SELECT IFNULL(SUM(qty),0) AS v FROM inventory")
    total_stock = float(cur.fetchone()["v"])

    # 음수 재고 row 수
    cur.execute("SELECT COUNT(*) AS c FROM inventory WHERE qty < 0")
    negative_rows = int(cur.fetchone()["c"])

    # 위치 미지정 qty 합
    cur.execute("""
        SELECT IFNULL(SUM(qty),0) AS v
        FROM inventory
        WHERE location IS NULL OR TRIM(location)=''
    """)
    no_location_qty = float(cur.fetchone()["v"])

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_rows": negative_rows,
        "no_location_qty": no_location_qty
    }


# =========================
# ✅ 로케이션 QR 스캔 → 해당 로케이션 재고 리스트
# =========================
def get_location_items(warehouse: str, location: str) -> List[Dict[str, Any]]:
    warehouse = (warehouse or "").strip() or "MAIN"
    location = (location or "").strip()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            warehouse,
            location,
            location_name,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            qty,
            updated_at
        FROM inventory
        WHERE warehouse=? AND location=?
        ORDER BY item_code, lot_no
    """, (warehouse, location))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
