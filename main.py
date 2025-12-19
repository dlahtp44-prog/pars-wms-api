from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

# =========================
# App 생성
# =========================
app = FastAPI(
    title="PARS WMS",
    description="입고, 출고, 재고이동, 재고조회, 작업이력, QR 스캔 WMS",
    version="1.0.0"
)

# =========================
# DB 초기화
# =========================
@app.on_event("startup")
def startup():
    from app.db import init_db
    init_db()
    print("✅ DB 초기화 완료")

# =========================
# 경로 설정
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
STATIC_DIR = os.path.join(APP_DIR, "static")
TEMPLATE_DIR = os.path.join(APP_DIR, "templates")

# static
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# templates (중요)
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
# Router 안전 등록 함수
# =========================
def safe_include(path: str):
    try:
        module = __import__(path, fromlist=["router"])
        app.include_router(module.router)
        print(f"✅ {path} 등록")
    except Exception as e:
        print(f"❌ {path} 실패:", e)

# =========================
# Page Routers (HTML)
# =========================
safe_include("app.pages.index_page")        # /
safe_include("app.pages.worker_page")       # /worker
safe_include("app.pages.inventory_page")    # /inventory-page
safe_include("app.pages.history_page")      # /history-page
safe_include("app.pages.qr_page")            # /qr-page
safe_include("app.pages.item_page")          # /item/{item_code}
safe_include("app.pages.upload_page")

# =========================
# API Routers
# =========================
safe_include("app.routers.items")
safe_include("app.routers.inbound")
safe_include("app.routers.outbound")
safe_include("app.routers.move")
safe_include("app.routers.inventory")
safe_include("app.routers.history")
safe_include("app.routers.location")
safe_include("app.routers.qr_api")
safe_include("app.routers.qr_process")
safe_include("app.routers.upload_inventory")
safe_include("app.routers.upload_outbound")


# =========================
# Health Check
# =========================
@app.get("/ping")
def ping():
    return {"status": "OK"}
