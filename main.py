from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os

# ------------------------------------------------------------
# APP INIT
# ------------------------------------------------------------
app = FastAPI(title="PARS WMS")

# ------------------------------------------------------------
# PATH SETTING
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")

# static / templates (존재할 때만 mount → Railway 안전)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.exists(TEMPLATE_DIR):
    templates = Jinja2Templates(directory=TEMPLATE_DIR)

# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# ROUTERS IMPORT
# ------------------------------------------------------------
from app.pages import (
    index_page,
    inbound_page,
    outbound_page,
    move_page,
    inventory_page,
    history_page,
    location_page,
    opening_page,
    admin_page,
    qr_page,          # ✅ QR 라벨 페이지
)

from app.routers import (
    inbound,
    outbound,
    move,
    inventory,
    history,
    location,
    items,
    qr_api,
)

# ------------------------------------------------------------
# ROUTERS REGISTER
# ------------------------------------------------------------
# 화면(Page)
app.include_router(index_page.router)
app.include_router(inbound_page.router)
app.include_router(outbound_page.router)
app.include_router(move_page.router)
app.include_router(inventory_page.router)
app.include_router(history_page.router)
app.include_router(location_page.router)
app.include_router(opening_page.router)
app.include_router(admin_page.router)
app.include_router(qr_page.router)      # ✅ /qr/label

# API
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(location.router)
app.include_router(items.router)
app.include_router(qr_api.router)

# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------
@app.get("/ping")
def ping():
    return {
        "status": "OK",
        "service": "PARS WMS",
        "message": "PARS WMS Running"
    }
