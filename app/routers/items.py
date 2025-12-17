from fastapi import APIRouter

router = APIRouter(tags=["품목"])

@router.get(
    "/items",
    summary="품목 조회",
    description="등록된 전체 품목을 조회합니다."
)
def get_items():
    return {"품목": []}

