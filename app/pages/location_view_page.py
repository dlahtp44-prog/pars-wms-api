# app/pages/location_view_page.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.db import get_locations

router = APIRouter(tags=["Location View"])

@router.get("/locations", response_class=HTMLResponse)
def location_list():
    locations = get_locations()

    rows = ""
    for loc in locations:
        rows += f"""
        <tr>
          <td>{loc['warehouse']}</td>
          <td>{loc['location']}</td>
          <td>
            <a class="btn"
               href="/label/location?paper=HEQ-3118&warehouse={loc['warehouse']}&location={loc['location']}"
               target="_blank">
               🖨 QR 라벨
            </a>
          </td>
        </tr>
        """

    return f"""
    <html>
    <head>
      <title>로케이션 관리</title>
      <link rel="stylesheet" href="/static/app.css">
    </head>
    <body>
      <h2>📍 로케이션 목록</h2>
      <table class="table">
        <thead>
          <tr>
            <th>창고</th>
            <th>로케이션</th>
            <th>라벨</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </body>
    </html>
    """
