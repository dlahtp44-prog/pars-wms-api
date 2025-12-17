from fastapi import APIRouter, Query

router = APIRouter(tags=["QR"])

@router.get(
    "/qr/label",
    summary="QR 라벨 생성",
    description="품목 QR 라벨을 생성합니다."
)
def qr_label(
    item_code: str = Query(..., title="품목 코드", example="ITEM001")
):
    return {"결과": "QR 라벨 생성 완료"}
