from fastapi import APIRouter

router = APIRouter(tags=["이력"])

@router.get(
    "/api/history",
    summary="작업 이력 조회",
    description="입·출고 및 이동 이력을 조회합니다."
)
def history():
    return {"이력": []}
