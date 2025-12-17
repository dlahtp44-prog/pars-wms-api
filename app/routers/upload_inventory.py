
from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app.db import get_conn

router = APIRouter(
    prefix="/api/upload",
    tags=["Excel Upload"]
)

@router.post("/inventory")
async def upload_inventory_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "엑셀(.xlsx) 파일만 업로드 가능합니다.")

    # 엑셀 읽기
    df = pd.read_excel(file.file)

    required_cols = [
        "장소명", "브랜드", "품번", "품명",
        "LOT NO", "규격", "로케이션", "현재고"
    ]

    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(400, f"엑셀 컬럼 누락: {col}")

    conn = get_conn()
    cur = conn.cursor()

    # 기존 재고 초기화 (초기 세팅용)
    cur.execute("DELETE FROM inventory")

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO inventory
            (warehouse, brand, item, item_name, lot, spec, location, qty)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["장소명"],
            row["브랜드"],
            str(row["품번"]),
            row["품명"],
            row["LOT NO"],
            row["규격"],
            row["로케이션"],
            int(row["현재고"])
        ))

    conn.commit()
    conn.close()

    return {
        "result": "OK",
        "message": f"{len(df)}건 재고 업로드 완료"
    }
