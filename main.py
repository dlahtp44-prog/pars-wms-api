from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# =========================
# App 설정
# =========================
app = FastAPI(
    title="PARS WMS",
    description="물류 입·출고, 이동, 재고, 작업이력 관리를 위한 WMS",
    version="1.0.0"
)

# =========================
# DB 초기화 (startup 이벤트)
# =========================
@app.on_event("startup")
def startup_event():
    try:
        from app.db import init_db
        init_db()
        print("✅ DB 초기화 완료")
    except Exception as e:
        print("❌ DB 초기화 실패:", e)

# =========================
# 경로 설정
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
TEMPLATE_DIR = os.path.join(BASE_DIR, "app", "templates")

# Static 파일
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates
if os.path.isdir(TEMPLATE_DIR):
    templates = Jinja2Templates(directory=TEMPLATE_DIR)

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
# Router 안전 등록 함수
# =========================
def safe_include(router_path: str, name: str):
    try:
        module = __import__(router_path, fromlist=["router"])
        app.include_router(module.router)
        print(f"✅ {name} router 등록")
    except Exception as e:
        print(f"❌ {name} router 로드 실패:", e)

# =========================
# API Routers
# =========================
safe_include("app.routers.items", "items")
safe_include("app.routers.inbound", "inbound")
safe_include("app.routers.outbound", "outbound")
safe_include("app.routers.move", "move")
safe_include("app.routers.location", "location")
safe_include("app.routers.inventory", "inventory")
safe_include("app.routers.history", "history")
safe_include("app.routers.qr_api", "qr_api")

# ❌ 엑셀 업로드 (pandas 의존 → 현재 비활성)
# safe_include("app.routers.upload_inventory", "upload_inventory")

# =========================
# Page Routers (HTML)
# =========================
safe_include("app.pages.index_page", "index_page")
safe_include("app.pages.worker_page", "worker_page")
safe_include("app.pages.inbound_page", "inbound_page")
safe_include("app.pages.outbound_page", "outbound_page")
safe_include("app.pages.move_page", "move_page")
safe_include("app.pages.inventory_page", "inventory_page")
safe_include("app.pages.history_page", "history_page")
safe_include("app.pages.qr_page", "qr_page")

# =========================
# Health Check
# =========================
@app.get(
    "/ping",
    summary="서버 상태 확인",
    description="서버가 정상 동작 중인지 확인합니다."
)
def ping():
    return {"status": "OK"}
