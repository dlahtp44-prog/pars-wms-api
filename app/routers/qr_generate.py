from fastapi import APIRouter

router = APIRouter(prefix="/api/label", tags=["라벨"])

# 실제 QR 이미지는 "브라우저에서 JS로 생성"하고, print로 출력한다.
# → 서버에 qrcode 모듈이 없어도 OK

@router.get("/product-3108")
def product_label_url(
    item_code: str,
    lot_no: str,
    item_name: str = "",
    spec: str = "",
    brand: str = ""
):
    # QR에는 최소만: item_code/lot_no/(선택) item_name/spec/brand
    # 스캔 후 작업 선택(입고/출고/이동)은 qr_page에서 처리
    return {
        "label_url": (
            f"/label/product-3108?"
            f"item_code={item_code}&lot_no={lot_no}&item_name={item_name}&spec={spec}&brand={brand}"
        )
    }

@router.get("/location-3118")
def location_label_url(location: str, warehouse: str = "MAIN"):
    return {"label_url": f"/label/location-3118?warehouse={warehouse}&location={location}"}
