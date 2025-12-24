from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app import db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/history-page", response_class=HTMLResponse)
async def history_page(request: Request):
    history = db.get_history(limit=200)
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>작업 이력</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>body { background-color: #f8f9fa; } .container { margin-top: 30px; }</style>
    </head>
    <body>
        <div class="container">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h4>📜 최근 작업 이력 (최근 200건)</h4>
                <a href="/api/export/history" class="btn btn-success">📊 이력 엑셀 다운로드</a>
            </div>
            <div class="table-responsive bg-white shadow-sm p-3 rounded">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>구분</th><th>위치</th><th>품번</th><th>LOT</th><th>수량</th><th>시간</th><th>비고</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for h in history %}
                        <tr>
                            <td><span class="badge {{ 'bg-primary' if h.tx_type=='IN' else 'bg-danger' if h.tx_type=='OUT' else 'bg-secondary' }}">{{ h.tx_type }}</span></td>
                            <td>{{ h.location or h.from_location ~ ' → ' ~ h.to_location }}</td>
                            <td>{{ h.item_code }}</td>
                            <td>{{ h.lot_no }}</td>
                            <td>{{ h.qty }}</td>
                            <td class="small">{{ h.created_at[:16].replace('T', ' ') }}</td>
                            <td>{{ h.remark or '' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return templates.TemplateResponse("history.html", {"request": request, "history": history}, block_start_string='{%', block_end_string='%}', variable_start_string='{{', variable_end_string='}}')
