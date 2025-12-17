from fastapi import APIRouter, Query

router = APIRouter(tags=["로케이션"])

@router.post(
    "/location/add",
    summary="로케이션 등록",
    description="새로운 로케이션을 등록합니다."
)
def add_location(
    location_code: str = Query(..., title="로케이션 코드", example="A01-01")
):
    return {"결과": "로케이션 등록 완료"}

@router.get(
    "/location/list",
    summary="로케이션 목록 조회",
    description="등록된 로케이션 목록을 조회합니다."
)
def list_locations():
    return {"로케이션목록": []}
