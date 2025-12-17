from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter(
    tags=["Page"],
    include_in_schema=False
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/move-page", response_class=HTMLResponse)
def move_page(request: Request):
    return templates.TemplateResponse(
        "move.html",
        {"request": request}
    )
