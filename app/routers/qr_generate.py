from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(prefix="/labels", tags=["QR Label"])

@router.get("/location", response_class=HTMLResponse)
def location_label(
    warehouse: str = Query("MAIN"),
    location: str = Query(...)
):
    """
    로케이션 QR 라벨 (HEQ-3118)
    """
    qr_data = urllib.parse.urlencode({
        "warehouse": warehouse,
        "location": location
    })

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {{
  size: 60mm 40mm;
  margin: 0;
}}
body {{
  margin: 0;
  padding: 4mm;
  font-family: Arial, sans-serif;
}}
.qr {{
  width: 30mm;
  height: 30mm;
}}
.loc {{
  font-size: 14px;
  font-weight: bold;
  margin-top: 4mm;
}}
</style>
</head>
<body onload="window.print()">
  <div style="text-align:center">
    <img class="qr"
      src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}">
    <div class="loc">{warehouse} / {location}</div>
  </div>
</body>
</html>
"""
