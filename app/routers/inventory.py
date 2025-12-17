from fastapi import APIRouter

router = APIRouter(tags=["재고"])

@router.get(
    "/inventory",
    summary="재고 현황 조회",
    description="현재 재고 현황을 조회합니다."
)
def inventory():
    return {"재고": []}
