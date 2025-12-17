from fastapi import APIRouter, Query

router = APIRouter(tags=["입고"])

@router.post(
    "/inbound",
    summary="입고 처리",
    description="상품 입고를 처리하는 API입니다."
)
def inbound(
    remark: str = Query(
        ...,
        title="입고 비고",
        description="입고 구분 또는 메모 (예: IN, 신규입고)",
        example="IN"
    )
):
    return {"결과": "입고 처리 완료"}
