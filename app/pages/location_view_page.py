from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/location-view")
def location_view(request: Request):
    return templates.TemplateResponse(
        "location_view.html",
        {"request": request}
    )
