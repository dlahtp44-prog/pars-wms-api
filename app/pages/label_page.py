# app/pages/label_page.py
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(tags=["Label"])

# ✅ HEQ-3108(제품): 50x30mm 가정
# ✅ HEQ-3118(로케이션): 70x40mm 가정
# 필요하면 숫자만 바꾸면 됨.
LABEL_SPECS = {
    "HEQ-3108": {"w_mm": 99.1, "h_mm": 38.1},  # 제품용
    "HEQ-3118": {"w_mm": 99.1, "h_mm": 140},  # 로케이션용
}

def qr_img_url(qr_text: str, size: int = 220) -> str:
    # 외부 QR 생성 (의존성 없음)
    # 데이터는 URL 인코딩 필수
    data = urllib.parse.quote(qr_text, safe="")
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={data}"

def safe(s: str) -> str:
    return (s or "").replace("<", "&lt;").replace(">", "&gt;")

@router.get("/label/product", response_class=HTMLResponse)
def label_product(
    # 라벨 크기 선택
    paper: str = Query("HEQ-3108"),
    # 제품 정보
    item_code: str = Query(...),
    lot_no: str = Query(""),
    item_name: str = Query(""),
    spec: str = Query(""),
    brand: str = Query(""),
    # QR 이동용 기본 수량 (옵션)
    qty: float = Query(1),
):
    spec_info = LABEL_SPECS.get(paper, LABEL_SPECS["HEQ-3108"])
    w_mm, h_mm = spec_info["w_mm"], spec_info["h_mm"]

    # ✅ 제품 QR 내용 (이동/출고/입고에서 공통으로 쓰기 좋게 type=ITEM)
    qr_text = urllib.parse.urlencode({
        "type": "ITEM",
        "item_code": item_code,
        "lot_no": lot_no,
        "qty": qty,
    })

    qr_url = qr_img_url(qr_text, size=240)

    return f"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>제품 QR 라벨 ({paper})</title>
  <style>
    @page {{
      size: {w_mm}mm {h_mm}mm;
      margin: 0;
    }}
    html, body {{
      width: {w_mm}mm;
      height: {h_mm}mm;
      margin: 0;
      padding: 0;
      font-family: Arial, "Malgun Gothic", sans-serif;
    }}
    .wrap {{
      box-sizing: border-box;
      width: 100%;
      height: 100%;
      padding: 2mm 2mm;
      display: grid;
      grid-template-columns: 1fr 18mm;
      gap: 1.5mm;
      align-items: center;
    }}
    .txt {{
      overflow: hidden;
    }}
    .line {{
      font-size: 9pt;
      line-height: 1.15;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .bold {{ font-weight: 800; }}
    .small {{ font-size: 8pt; color: #111; }}
    .qr {{
      width: 18mm;
      height: 18mm;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .qr img {{
      width: 18mm;
      height: 18mm;
      image-rendering: pixelated;
    }}
    .hint {{
      margin-top: 1mm;
      font-size: 7pt;
      color: #444;
    }}
    /* 인쇄 버튼은 인쇄 시 숨김 */
    .actions {{
      position: fixed;
      left: 8px;
      bottom: 8px;
      display: flex;
      gap: 8px;
      z-index: 9999;
    }}
    .btn {{
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #e5e7eb;
      background: #111827;
      color: #fff;
      font-size: 14px;
    }}
    @media print {{
      .actions {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="txt">
      <div class="line bold">품번: {safe(item_code)}</div>
      <div class="line">LOT: {safe(lot_no)}</div>
      <div class="line">품명: {safe(item_name)}</div>
      <div class="line">규격: {safe(spec)}</div>
      <div class="line">브랜드: {safe(brand)}</div>
    </div>
    <div class="qr">
      <img src="{qr_url}" alt="QR" />
    </div>
  </div>

  <div class="actions">
    <button class="btn" onclick="window.print()">라벨 인쇄 / PDF 저장</button>
  </div>
</body>
</html>
"""


@router.get("/label/location", response_class=HTMLResponse)
def label_location(
    paper: str = Query("HEQ-3118"),
    warehouse: str = Query("MAIN"),
    location: str = Query(...),
):
    spec_info = LABEL_SPECS.get(paper, LABEL_SPECS["HEQ-3118"])
    w_mm, h_mm = spec_info["w_mm"], spec_info["h_mm"]

    # ✅ 로케이션 QR 내용 (type=LOC)
    qr_text = urllib.parse.urlencode({
        "type": "LOC",
        "warehouse": warehouse,
        "location": location,
    })

    qr_url = qr_img_url(qr_text, size=300)

    return f"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>로케이션 QR 라벨 ({paper})</title>
  <style>
    @page {{
      size: {w_mm}mm {h_mm}mm;
      margin: 0;
    }}
    html, body {{
      width: {w_mm}mm;
      height: {h_mm}mm;
      margin: 0;
      padding: 0;
      font-family: Arial, "Malgun Gothic", sans-serif;
    }}
    .wrap {{
      width: 100%;
      height: 100%;
      box-sizing: border-box;
      padding: 3mm 3mm;
      display: grid;
      grid-template-columns: 1fr 28mm;
      gap: 2mm;
      align-items: center;
    }}
    .loc {{
      font-weight: 900;
      font-size: 18pt;
      letter-spacing: 0.5px;
      line-height: 1;
    }}
    .sub {{
      margin-top: 2mm;
      font-size: 9pt;
      color: #111;
    }}
    .qr {{
      width: 28mm;
      height: 28mm;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .qr img {{
      width: 28mm;
      height: 28mm;
      image-rendering: pixelated;
    }}
    .actions {{
      position: fixed;
      left: 8px;
      bottom: 8px;
      display: flex;
      gap: 8px;
      z-index: 9999;
    }}
    .btn {{
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #e5e7eb;
      background: #111827;
      color: #fff;
      font-size: 14px;
    }}
    @media print {{
      .actions {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div>
      <div class="loc">{safe(location)}</div>
      <div class="sub">창고: {safe(warehouse)}</div>
    </div>
    <div class="qr">
      <img src="{qr_url}" alt="QR" />
    </div>
  </div>

  <div class="actions">
    <button class="btn" onclick="window.print()">라벨 인쇄 / PDF 저장</button>
  </div>
</body>
</html>
"""
