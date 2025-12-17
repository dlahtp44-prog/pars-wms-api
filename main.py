from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# =========================
# DB 초기화 (중요)
# =========================
from app.db import init_db
init_db()

# =========================
# App 설정
# =========================
app = FastAPI(
    title="PARS WMS",
    description="물류 입·출고, 이동, 재고, 작업이력, 엑셀업로드를 포함한 WMS",
    version="1.0.0"
)

# =========================
# 경로 설정
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")

# Static (CSS / JS)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates (HTML)
if os.path.exists(TEMPLATE_DIR):
    templates = Jinja2Templates(directory=TEMPLATE_DIR)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# API Routers
# =========================
from app.routers.items import router as items_router
from app.routers.inbound import router as inbound_router
from app.routers.outbound import router as outbound_router
from app.routers.move import router as move_router
from app.routers.location import router as location_router
from app.routers.inventory import router as inventory_router
from app.routers.history import router as history_router
from app.routers.qr_api import router as qr_router
from app.routers.upload_inventory import router as upload_inventory_router

# =========================
# Page Routers (HTML)
# =========================
from app.pages.index_page import router as index_page_router
from app.pages.worker_page import router as worker_page_router
from app.pages.inbound_page import router as inbound_page_router
from app.pages.outbound_page import router as outbound_page_router
from app.pages.move_page import router as move_page_router
from app.pages.inventory_page import router as inventory_page_router
from app.pages.history_page import router as history_page_router
from app.pages.qr_page import router as qr_page_router

# =========================
# Router 등록
# =========================

# 메인 / 작업자
app.include_router(index_page_router)
app.include_router(worker_page_router)

# 페이지
app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(qr_page_router)

# API
app.include_router(items_router)
app.include_router(inbound_router)
app.include_router(outbound_router)
app.include_router(move_router)
app.include_router(location_router)
app.include_router(inventory_router)
app.include_router(history_router)
app.include_router(qr_router)
app.include_router(upload_inventory_router)

# =========================
# Health Check
# =========================
@app.get(
    "/ping",
    summary="서버 상태 확인",
    description="서버가 정상 동작 중인지 확인"
)
def ping():
    return {"상태": "정상"}
