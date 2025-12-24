# app/db.py
import os
import sqlite3
import hmac
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.getenv("DB_PATH", "WMS.db")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")  # Railway ENV로 꼭 바꾸세요

# =========================
# DB Connection
# =========================
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# DB Init
# =========================
def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    # inventory (재고)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT NOT NULL,
            location TEXT NOT NULL,
            brand TEXT DEFAULT '',
            item_code TEXT NOT NULL,
            item_name TEXT DEFAULT '',
            lot_no TEXT NOT NULL,
            spec TEXT DEFAULT '',
            qty REAL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(warehouse, location, item_code, lot_no)
        )
        """
    )

    # history (이력)
    # - 이동(from/to), 품명/규격/브랜드까지 같이 넣어야 롤백/대시보드가 안정적임
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_type TEXT NOT NULL,               -- IN / OUT / MOVE / ROLLBACK / ...
            warehouse TEXT DEFAULT '',
            location TEXT DEFAULT '',            -- IN/OUT 기준 location
            from_location TEXT DEFAULT '',       -- MOVE 기준
            to_location TEXT DEFAULT '',         -- MOVE 기준
            brand TEXT DEFAULT '',
            item_code TEXT DEFAULT '',
            item_name TEXT DEFAULT '',
            lot_no TEXT DEFAULT '',
            spec TEXT DEFAULT '',
            qty REAL DEFAULT 0,
            remark TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # 속도용 인덱스
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inv_item ON inventory(item_code, lot_no)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_inv_loc ON inventory(location)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hist_date ON history(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_hist_item ON history(item_code, lot_no)")

    conn.commit()
    conn.close()


# =========================
# Admin password
# =========================
def admin_password_ok(pw: str) -> bool:
    # timing attack 방지
    return hmac.compare_digest(str(pw or ""), str(ADMIN_PASSWORD))


# =========================
# Inventory Queries
# =========================
def get_inventory(
    warehouse: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 2000,
) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT
            warehouse,
            location,
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
        kw = f"%{q}%"
        sql += """
            AND (
                item_code LIKE ?
                OR item_name LIKE ?
                OR lot_no LIKE ?
                OR brand LIKE ?
                OR spec LIKE ?
                OR location LIKE ?
            )
        """
        params.extend([kw, kw, kw, kw, kw, kw])

    sql += " ORDER BY updated_at DESC, item_code ASC LIMIT ?"
    params.append(int(limit))

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_location_items(location: str, warehouse: str = "MAIN") -> List[Dict[str, Any]]:
    """로케이션 QR 찍으면 해당 위치 재고 리스트 바로 보여주기"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at
        FROM inventory
        WHERE warehouse=? AND location=?
        ORDER BY item_code, lot_no
        """,
        (warehouse, location),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# History Queries
# =========================
def get_history(limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM history
        ORDER BY id DESC
        LIMIT ?
        """,
        (int(limit),),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# log_history (호환성 최우선)
# =========================
def log_history(*args, **kwargs) -> None:
    """
    프로젝트에서 호출 방식이 섞여 있어 "모든 패턴"을 받아줌.

    패턴 A (신형):
      log_history("IN", wh, loc, item_code, lot_no, qty, remark)

    패턴 B (구형/확장형):
      log_history("입고", wh, loc, item_code, item_name, lot_no, spec, qty, remark)

    키워드형:
      log_history(tx_type="IN", warehouse="MAIN", location="A01", item_code="...", lot_no="...", qty=1, remark="...")
    """
    tx_type = ""
    warehouse = ""
    location = ""
    from_location = ""
    to_location = ""
    brand = ""
    item_code = ""
    item_name = ""
    lot_no = ""
    spec = ""
    qty = 0.0
    remark = ""

    # 1) kwargs 우선
    if kwargs:
        tx_type = str(kwargs.get("tx_type", kwargs.get("type", "")) or "")
        warehouse = str(kwargs.get("warehouse", "MAIN") or "MAIN")
        location = str(kwargs.get("location", "") or "")
        from_location = str(kwargs.get("from_location", "") or "")
        to_location = str(kwargs.get("to_location", "") or "")
        brand = str(kwargs.get("brand", "") or "")
        item_code = str(kwargs.get("item_code", "") or "")
        item_name = str(kwargs.get("item_name", "") or "")
        lot_no = str(kwargs.get("lot_no", "") or "")
        spec = str(kwargs.get("spec", "") or "")
        qty = float(kwargs.get("qty", 0) or 0)
        remark = str(kwargs.get("remark", "") or "")

    # 2) args 패턴 파싱
    if args:
        # 최소 tx_type은 args[0]로 덮어씀(혼합 호출 보호)
        tx_type = str(args[0] or tx_type)

        # A: (tx_type, wh, loc, item_code, lot_no, qty, remark)
        if len(args) >= 7:
            warehouse = str(args[1] or warehouse or "MAIN")
            location = str(args[2] or location)
            item_code = str(args[3] or item_code)
            lot_no = str(args[4] or lot_no)
            qty = float(args[5] or qty or 0)
            remark = str(args[6] or remark)

        # B: (tx_type, wh, loc, item_code, item_name, lot_no, spec, qty, remark)
        if len(args) >= 9:
            warehouse = str(args[1] or warehouse or "MAIN")
            location = str(args[2] or location)
            item_code = str(args[3] or item_code)
            item_name = str(args[4] or item_name)
            lot_no = str(args[5] or lot_no)
            spec = str(args[6] or spec)
            qty = float(args[7] or qty or 0)
            remark = str(args[8] or remark)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location, brand, item_code, item_name, lot_no, spec, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tx_type,
            warehouse,
            location,
            from_location,
            to_location,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            qty,
            remark,
        ),
    )
    conn.commit()
    conn.close()


# =========================
# Inventory Mutations
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
    remark: str = "입고",
) -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            brand=excluded.brand,
            item_name=excluded.item_name,
            spec=excluded.spec,
            qty = inventory.qty + excluded.qty,
            updated_at=CURRENT_TIMESTAMP
        """,
        (warehouse, location, brand or "", item_code, item_name or "", lot_no, spec or "", float(qty)),
    )

    log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        brand=brand or "",
        item_code=item_code,
        item_name=item_name or "",
        lot_no=lot_no,
        spec=spec or "",
        qty=float(qty),
        remark=str(remark or "입고"),
    )

    conn.commit()
    conn.close()


def subtract_inventory(
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "출고",
    block_negative: bool = False,  # ✅ 라우터에서 쓰던 키워드 지원
) -> None:
    conn = get_conn()
    cur = conn.cursor()

    # 현재 수량 확인
    cur.execute(
        """
        SELECT qty, brand, item_name, spec
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """,
        (warehouse, location, item_code, lot_no),
    )
    row = cur.fetchone()

    current_qty = float(row["qty"]) if row else 0.0
    brand = str(row["brand"]) if row else ""
    item_name = str(row["item_name"]) if row else ""
    spec = str(row["spec"]) if row else ""

    new_qty = current_qty - float(qty)

    if block_negative and new_qty < 0:
        conn.close()
        raise ValueError(f"음수 재고 차단: 현재 {current_qty}, 출고 {qty}")

    if row:
        cur.execute(
            """
            UPDATE inventory
            SET qty=?, updated_at=CURRENT_TIMESTAMP
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
            """,
            (new_qty, warehouse, location, item_code, lot_no),
        )
    else:
        # 없는데 출고가 들어오면 음수로 생성(원하면 block_negative로 차단)
        cur.execute(
            """
            INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (warehouse, location, brand, item_code, item_name, lot_no, spec, new_qty),
        )

    log_history(
        tx_type="OUT",
        warehouse=warehouse,
        location=location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=float(qty),
        remark=str(remark or "출고"),
    )

    conn.commit()
    conn.close()


def move_inventory(
    warehouse: str,
    item_code: str,
    lot_no: str,
    from_location: str,
    to_location: str,
    qty: float,
    remark: str = "이동",
    block_negative: bool = True,
) -> None:
    """
    이동 = from_location에서 차감 + to_location에 증가
    """
    # 1) from 차감
    subtract_inventory(
        warehouse=warehouse,
        location=from_location,
        item_code=item_code,
        lot_no=lot_no,
        qty=float(qty),
        remark=f"{remark}(FROM)",
        block_negative=block_negative,
    )

    # 2) to 증가 (from의 메타 정보 가져와서 같이)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT brand, item_name, spec
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """,
        (warehouse, from_location, item_code, lot_no),
    )
    meta = cur.fetchone()
    conn.close()

    brand = str(meta["brand"]) if meta else ""
    item_name = str(meta["item_name"]) if meta else ""
    spec = str(meta["spec"]) if meta else ""

    add_inventory(
        warehouse=warehouse,
        location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=float(qty),
        remark=f"{remark}(TO)",
    )

    # MOVE 이력 별도 기록(롤백용)
    log_history(
        tx_type="MOVE",
        warehouse=warehouse,
        location="",
        from_location=from_location,
        to_location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=float(qty),
        remark=str(remark or "이동"),
    )


# =========================
# Rollback
# =========================
def rollback(tx_id: int) -> None:
    """
    history의 한 건을 되돌림
    - IN  -> 같은 위치에서 qty 만큼 출고(차감)
    - OUT -> 같은 위치에 qty 만큼 입고(증가)
    - MOVE -> to에서 차감 + from에 증가
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (int(tx_id),))
    h = cur.fetchone()
    if not h:
        conn.close()
        raise ValueError("기록 없음")

    tx_type = str(h["tx_type"] or "")
    warehouse = str(h["warehouse"] or "MAIN")
    location = str(h["location"] or "")
    from_location = str(h["from_location"] or "")
    to_location = str(h["to_location"] or "")
    brand = str(h["brand"] or "")
    item_code = str(h["item_code"] or "")
    item_name = str(h["item_name"] or "")
    lot_no = str(h["lot_no"] or "")
    spec = str(h["spec"] or "")
    qty = float(h["qty"] or 0)

    conn.close()

    if tx_type == "IN":
        subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=f"ROLLBACK(IN:{tx_id})", block_negative=False)
    elif tx_type == "OUT":
        add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=f"ROLLBACK(OUT:{tx_id})")
    elif tx_type == "MOVE":
        # MOVE는 to에서 빼고 from으로 돌림
        subtract_inventory(warehouse, to_location, item_code, lot_no, qty, remark=f"ROLLBACK(MOVE:{tx_id})", block_negative=False)
        add_inventory(warehouse, from_location, brand, item_code, item_name, lot_no, spec, qty, remark=f"ROLLBACK(MOVE:{tx_id})")
    else:
        # 기타는 그냥 기록만 남김
        log_history(tx_type="ROLLBACK", warehouse=warehouse, location=location, item_code=item_code, lot_no=lot_no, qty=0, remark=f"UNSUPPORTED:{tx_type}:{tx_id}")
        return

    log_history(
        tx_type="ROLLBACK",
        warehouse=warehouse,
        location=location,
        from_location=from_location,
        to_location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=f"rollback tx_id={tx_id}",
    )


# =========================
# Dashboard
# =========================
def dashboard_summary() -> Tuple[float, float, float, int]:
    """
    기존 dashboard_page에서
      inbound, outbound, total, negative = dashboard_summary()
    이렇게 언패킹하는 형태를 그대로 지원
    """
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 IN
    cur.execute(
        """
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN'
          AND DATE(created_at)=DATE('now','localtime')
        """
    )
    inbound_today = float(cur.fetchone()[0] or 0)

    # 오늘 OUT
    cur.execute(
        """
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT'
          AND DATE(created_at)=DATE('now','localtime')
        """
    )
    outbound_today = float(cur.fetchone()[0] or 0)

    # 총 재고
    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = float(cur.fetchone()[0] or 0)

    # 음수 재고 건수
    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative_cnt = int(cur.fetchone()[0] or 0)

    conn.close()
    return inbound_today, outbound_today, total_stock, negative_cnt
