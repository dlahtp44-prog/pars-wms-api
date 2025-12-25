# app/pages/label_page.py

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import urllib.parse

router = APIRouter(prefix="/label", tags=["Label"])

# ============================
# 📍 로케이션 QR 라벨 (HEQ-3118)
# ============================
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
        <meta charset="utf-8">
        <title>Location QR</title>
        <style>
            @page {{
                size: 70mm 40mm;
                margin: 0;
            }}
            body {{
                margin: 0;
                padding: 4mm;
                font-family: Arial, sans-serif;
                text-align: center;
            }}
            img {{
                width: 30mm;
                height: 30mm;
            }}
            .loc {{
                margin-top: 3mm;
                font-size: 16px;
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
