from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app.db import get_conn, log_history

router = APIRouter(prefix="/api/upload", tags=["엑셀업로드"])

REQUIRED_COLUMNS = [
    "장소명", "브랜드", "품번", "품명",
    "LOT", "규격", "로케이션", "수량"
]

@router.post("/inventory-xlsx")
async def upload_inventory_xlsx(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="xlsx 파일만 업로드 가능")

    try:
        df = pd.read_excel(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"엑셀 읽기 실패: {e}")

    # 컬럼 검증
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {col}")

    conn = get_conn()
    cur = conn.cursor()

    for idx, row in df.iterrows():
        try:
            qty = int(row["수량"])

            cur.execute("""
                INSERT INTO inventory
                (location_name, brand, item_code, item_name, lot_no, spec, location, qty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(item_code, location)
                DO UPDATE SET qty = qty + excluded.qty
            """, (
                row["장소명"],
                row["브랜드"],
                row["품번"],
                row["품명"],
                row["LOT"],
                row["규격"],
                row["로케이션"],
                qty
            ))

            log_history(
                "엑셀입고",
                row["품번"],
                qty,
                row["로케이션"]
            )

        except Exception as e:
            conn.rollback()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"{idx+2}행 처리 실패: {e}"
            )

    conn.commit()
    conn.close()

    return {
        "result": "엑셀 업로드 완료",
        "rows": len(df)
    }
