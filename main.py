from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="PARS WMS")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")

if os.path.exists(TEMPLATE_DIR):
    templates = Jinja2Templates(directory=TEMPLATE_DIR)
else:
    templates = None


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 각 router를 직접 import (중요)
from app.routers.items import router as items_router
from app.routers.inbound import router as inbound_router
from app.routers.outbound import router as outbound_router
from app.routers.move import router as move_router
from app.routers.location import router as location_router
from app.routers.inventory import router as inventory_router
from app.routers.history import router as history_router
from app.routers.qr_api import router as qr_router

# 페이지
from app.pages.index_page import router as index_router
from app.pages.qr_page import router as qr_page_router

# 등록
app.include_router(index_router)
app.include_router(items_router)
app.include_router(inbound_router)
app.include_router(outbound_router)
app.include_router(move_router)
app.include_router(location_router)
app.include_router(inventory_router)
app.include_router(history_router)
app.include_router(qr_router)
app.include_router(qr_page_router)

@app.get("/ping")
def ping():
    return {"status": "OK"}
