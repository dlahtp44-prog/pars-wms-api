# app/routers/qr_generate.py
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from urllib.parse import quote

router = APIRouter(prefix="/api/qr", tags=["qr-label"])

def qr_img(data: str, size: int = 220) -> str:
    # 외부 QR 생성 서비스(간단/무설치)
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={quote(data)}"

@router.get("/label/item", response_class=HTMLResponse)
def item_label(
    item_code: str = Query(...),
    lot_no: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    brand: str = Query(""),
):
    # 제품 라벨(HEQ-3108): 품번/LOT/품명/규격/브랜드 + QR(필드 포함)
    qr_data = f"type=ITEM&item_code={item_code}&lot_no={lot_no}&item_name={item_name}&spec={spec}&brand={brand}&qty=1"
    img = qr_img(qr_data, 240)

    return f"""
<!doctype html><html lang="ko"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HEQ-3108 제품 라벨</title>
<style>
@page{{ size: 38mm 28mm; margin: 0; }} /* HEQ-3108 근사(필요시 수정) */
body{{ margin:0; font-family:Arial; }}
.wrap{{ width:38mm; height:28mm; padding:1.5mm; box-sizing:border-box; display:flex; gap:1.5mm; }}
.left{{ flex:1; font-size:7px; line-height:1.15; overflow:hidden; }}
.qr{{ width:18mm; height:18mm; }}
.qr img{{ width:18mm; height:18mm; }}
.b{{ font-weight:800; }}
</style></head>
<body onload="window.print()">
<div class="wrap">
  <div class="left">
    <div class="b">품번:{item_code}</div>
    <div class="b">LOT:{lot_no}</div>
    <div>품명:{item_name}</div>
    <div>규격:{spec}</div>
    <div>브랜드:{brand}</div>
  </div>
  <div class="qr"><img src="{img}"/></div>
</div>
</body></html>
"""

@router.get("/label/location", response_class=HTMLResponse)
def location_label(
    location: str = Query(...),
    warehouse: str = Query("MAIN"),
):
    # 로케이션 라벨(HEQ-3118): 위치 + QR(LOC)
    qr_data = f"type=LOC&warehouse={warehouse}&location={location}"
    img = qr_img(qr_data, 300)

    return f"""
<!doctype html><html lang="ko"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HEQ-3118 로케이션 라벨</title>
<style>
@page{{ size: 50mm 30mm; margin: 0; }} /* HEQ-3118 근사(필요시 수정) */
body{{ margin:0; font-family:Arial; }}
.wrap{{ width:50mm; height:30mm; padding:2mm; box-sizing:border-box; display:flex; align-items:center; justify-content:space-between; }}
.loc{{ font-size:14px; font-weight:900; }}
.qr img{{ width:24mm; height:24mm; }}
</style></head>
<body onload="window.print()">
<div class="wrap">
  <div class="loc">{location}</div>
  <div class="qr"><img src="{img}"/></div>
</div>
</body></html>
"""
