from fastapi import APIRouter, Query

router = APIRouter(tags=["출고"])

@router.post(
    "/outbound",
    summary="출고 처리",
    description="상품 출고를 처리하는 API입니다."
)
def outbound(
    remark: str = Query(
        ...,
        title="비고",
        description="출고 구분 또는 메모 (예: OUT, 판매출고)",
        example="OUT"
    )
):
    return {"결과": "출고 처리 완료"}
