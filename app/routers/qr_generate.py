from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(prefix="/labels", tags=["QR Label"])

@router.get("/location", response_class=HTMLResponse)
def location_qr(
    warehouse: str = "MAIN",
    location: str = Query(...)
):
    qr_data = urllib.parse.urlencode({
        "warehouse": warehouse,
        "location": location
    })

    return f"""
    <html>
    <head>
      <style>
        @page {{ size: 70mm 40mm; margin: 0; }}
        body {{
          font-family: Arial;
          text-align: center;
          margin: 0;
          padding: 4mm;
        }}
        img {{ width: 30mm; height: 30mm; }}
        .loc {{ font-size: 14px; font-weight: bold; margin-top: 4px; }}
      </style>
    </head>
    <body>
      <img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}">
      <div class="loc">{location}</div>
    </body>
    </html>
    """
