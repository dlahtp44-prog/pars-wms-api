from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/worker/inbound")
def worker_inbound(request: Request):
    return templates.TemplateResponse(
        "worker_inbound.html",
        {"request": request}
    )
