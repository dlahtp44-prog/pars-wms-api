from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.pages import index_page
from app.routers import (
    items, inbound, outbound, move, location,
    inventory, history, qr_api
)
import os

app = FastAPI(title="PARS WMS - Responsive + QR + Label 70x40")

# ------------------------------------------------------------
# STATIC & TEMPLATE PATHS
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 필요 시 도메인 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# ROUTERS
# ------------------------------------------------------------
app.include_router(index_page.router)
app.include_router(items.router)
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(location.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(qr_api.router)

@app.get("/ping")
def ping():
    return {"status": "OK", "msg": "PARS WMS Running"}

