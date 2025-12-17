from fastapi import APIRouter

router = APIRouter(tags=["이력"])

@router.get(
    "/api/history",
    summary="작업 이력 조회",
    description="입고, 출고, 이동 이력을 조회합니다."
)
def history():
    return {"작업이력": []}

@router.post(
    "/api/history/rollback",
    summary="작업 롤백",
    description="최근 작업을 롤백 처리합니다."
)
def rollback():
    return {"결과": "롤백 완료"}
