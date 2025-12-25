from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from urllib.parse import parse_qs

router = APIRouter(prefix="/api/qr")

@router.get("/search")
def qr_search(qr: str):
    params = parse_qs(qr)

    if "location" in params:
        loc = params["location"][0]
        return RedirectResponse(f"/location/{loc}")

    return {"error": "알 수 없는 QR"}
