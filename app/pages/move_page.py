from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/move")
def move_page(request: Request):
    return templates.TemplateResponse(
        "move.html",
        {"request": request}
    )
