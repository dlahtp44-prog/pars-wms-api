from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# =========================
# App 기본 설정
# =========================
app = FastAPI(
    title="PARS WMS",
    description="물류 입·출고, 이동, 재고 관리를 위한 WMS API",
    version="1.0.0"
)

# =========================
# 경로 설정
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")

# Static 파일 (CSS, JS)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Template (HTML)
if os.path.exists(TEMPLATE_DIR):
    templates = Jinja2Templates(directory=TEMPLATE_DIR)
else:
    templates = None

# =========================
# CORS 설정
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# API Router import
# =========================
from app.pages.index_page import router as index_router
from app.pages.worker_page import router as worker_router
from app.pages.inbound_page import router as inbound_page_router
from app.pages.outbound_page import router as outbound_page_router
from app.pages.move_page import router as move_page_router
from app.pages.inventory_page import router as inventory_page_router
from app.pages.history_page import router as history_page_router
from app.pages.qr_page import router as qr_page_router

# =========================
# Page Router import
# =========================
from app.pages.index_page import router as index_router
from app.pages.qr_page import router as qr_page_router
from app.pages.worker_page import router as worker_router  # 작업자 화면
from app.pages.inbound_page import router as inbound_page_router
from app.pages.move_page import router as move_page_router
app.include_router(move_page_router)


# =========================
# Router 등록
# =========================
app.include_router(index_router)
app.include_router(worker_router)

app.include_router(inbound_page_router)
app.include_router(outbound_page_router)
app.include_router(move_page_router)
app.include_router(inventory_page_router)
app.include_router(history_page_router)
app.include_router(qr_page_router)

# =========================
# Health Check
# =========================
@app.get(
    "/ping",
    summary="서버 상태 확인",
    description="서버가 정상적으로 동작 중인지 확인합니다."
)
def ping():
    return {"상태": "정상"}
