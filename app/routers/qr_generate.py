from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(prefix="/label", tags=["QR Label"])

@router.get("/location", response_class=HTMLResponse)
def location_label(
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
        @page {{
          size: 70mm 40mm;   /* HEQ-3118 */
          margin: 0;
        }}
        body {{
          margin: 0;
          padding: 4mm;
          font-family: Arial, sans-serif;
          text-align: center;
        }}
        img {{
          width: 28mm;
          height: 28mm;
        }}
        .loc {{
          margin-top: 2mm;
          font-size: 14px;
          font-weight: bold;
        }}
      </style>
    </head>
    <body>
      <img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}">
      <div class="loc">{location}</div>
    </body>
    </html>
    """
