from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(prefix="/label", tags=["QR Label"])

# =========================
# 제품 QR (HEQ-3108)
# =========================
@router.get("/product", response_class=HTMLResponse)
def product_label(
    item_code: str,
    item_name: str = "",
    spec: str = "",
    lot_no: str = "",
    brand: str = ""
):
    qr_data = urllib.parse.urlencode({
        "item_code": item_code,
        "item_name": item_name,
        "spec": spec,
        "lot_no": lot_no,
        "brand": brand
    })

    return f"""
    <html>
    <head>
      <style>
        @page {{ size: 50mm 30mm; margin: 0; }}
        body {{
          margin:0; padding:4mm;
          font-family: Arial, sans-serif;
          font-size:9px;
        }}
        .wrap {{ display:flex; gap:4mm; }}
        img {{ width:22mm; height:22mm; }}
        .t {{ line-height:1.3; }}
        .b {{ font-weight:bold; }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}">
        <div class="t">
          <div class="b">{item_code}</div>
          <div>{item_name}</div>
          <div>{spec}</div>
          <div>LOT: {lot_no}</div>
          <div>{brand}</div>
        </div>
      </div>
    </body>
    </html>
    """
