from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.db import get_inventory

router = APIRouter(tags=["Inventory Page"])

@router.get("/inventory-page", response_class=HTMLResponse)
def inventory_page():
    items = get_inventory()

    rows = ""
    for it in items:
        rows += f"""
        <tr>
          <td>{it['item_code']}</td>
          <td>{it['item_name']}</td>
          <td>{it['lot_no']}</td>
          <td>{it['spec']}</td>
          <td>{it['brand']}</td>
          <td>{it['qty']}</td>
          <td>
            <a class="btn"
               href="/label/product?paper=HEQ-3108
               &item_code={it['item_code']}
               &lot_no={it['lot_no']}
               &item_name={it['item_name']}
               &spec={it['spec']}
               &brand={it['brand']}"
               target="_blank">
               🏷 QR 라벨
            </a>
          </td>
        </tr>
        """

    return f"""
    <html>
    <head>
      <title>재고 현황</title>
      <link rel="stylesheet" href="/static/app.css">
    </head>
    <body>
      <h2>📦 재고 현황</h2>

      <a class="btn" href="/api/export/inventory">📥 재고 엑셀</a>

      <table class="table">
        <thead>
          <tr>
            <th>품번</th>
            <th>품명</th>
            <th>LOT</th>
            <th>규격</th>
            <th>브랜드</th>
            <th>수량</th>
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
