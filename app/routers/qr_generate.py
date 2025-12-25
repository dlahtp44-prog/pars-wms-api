from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(prefix="/labels", tags=["QR Label"])

@router.get("/product", response_class=HTMLResponse)
def product_label(
    item_code: str = Query(...),
    lot_no: str = Query(...),
    item_name: str = Query(""),
    spec: str = Query(""),
    brand: str = Query(""),
    warehouse: str = Query("MAIN"),
    location: str = Query("")   # ← 추가
):
    """
    제품 QR 라벨 (HEQ-3108 : 50x30mm)
    """

    qr_data = urllib.parse.urlencode({
        "warehouse": warehouse,
        "location": location,
        "item_code": item_code,
        "lot_no": lot_no,
        "item_name": item_name,
        "spec": spec,
        "brand": brand
    })

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: 50mm 30mm;
  margin: 0;
}}
body {{
  margin: 0;
  padding: 2mm;
  font-family: Arial, sans-serif;
  font-size: 8px;
}}
.wrapper {{
  display: flex;
  align-items: center;
}}
.qr {{
  width: 22mm;
  height: 22mm;
}}
.info {{
  margin-left: 2mm;
  line-height: 1.2;
}}
.code {{
  font-weight: bold;
  font-size: 9px;
}}
.loc {{
  font-size: 7px;
  color: #555;
}}
</style>
</head>
<body onload="window.print()">
  <div class="wrapper">
    <img class="qr"
      src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}">
    <div class="info">
      <div class="code">{item_code}</div>
      <div>LOT: {lot_no}</div>
      <div>{item_name}</div>
      <div>{spec}</div>
      <div>{brand}</div>
      <div class="loc">{warehouse} {location}</div>
    </div>
  </div>
</body>
</html>
"""
