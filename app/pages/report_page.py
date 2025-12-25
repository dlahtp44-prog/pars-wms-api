from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.db import get_inventory
from datetime import date

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/report/a3")
def report_a3(request: Request):
    rows = get_inventory()

    summary = {}
    for r in rows:
        summary[r[1]] = summary.get(r[1], 0) + r[6]

    return templates.TemplateResponse(
        "report_a3_graph.html",
        {
            "request": request,
            "today": date.today(),
            "rows": rows,
            "summary": summary
        }
    )
