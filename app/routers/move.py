from fastapi import APIRouter, Query

router = APIRouter(
    prefix="/move",
    tags=["재고이동"]
)

@router.post(
    "",
    summary="재고 이동 처리",
    description="재고를 다른 로케이션으로 이동합니다."
)
def move(
    remark: str = Query(
        ...,
        title="이동 구분",
        description="재고 이동 메모 또는 코드 (예: MOVE, 재고이동)"
    )
):
    return {"결과": f"재고 이동 처리 완료 ({remark})"}
