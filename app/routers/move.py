from fastapi import APIRouter, Query

router = APIRouter(tags=["재고이동"])

@router.post(
    "/move",
    summary="재고 이동",
    description="창고 또는 위치 간 재고 이동을 처리합니다."
)
def move(
    from_loc: str = Query(..., title="출발 위치", example="A01-01"),
    to_loc: str = Query(..., title="도착 위치", example="B01-02"),
):
    return {"결과": "재고 이동 완료"}
