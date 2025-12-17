from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# ------------------------------------------------------------
# Router
# ------------------------------------------------------------
router = APIRouter(
    prefix="/history",
    tags=["Page"],
    include_in_schema=False
)

# ------------------------------------------------------------
# Template Path
# main.py 기준으로 templates 경로 계산
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# ------------------------------------------------------------
# Page
# ------------------------------------------------------------
@router.get("", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse(
        "history.html",
        {
            "request": request
        }
    )

