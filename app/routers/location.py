from fastapi import APIRouter
from app.core.locations import WAREHOUSE_MAP

router = APIRouter(
    prefix="/api",
    tags=["로케이션"]
)

@router.get(
    "/locations",
    summary="로케이션 구조 조회",
    description="창고 → 존 → 랙 → 셀 전체 구조를 반환합니다."
)
def get_locations():
    return WAREHOUSE_MAP
