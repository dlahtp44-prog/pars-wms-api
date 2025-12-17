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
    description="입고·출고·재고이동·재고조회·작업이력·QR 기반 WMS",
    version="1.0.0"
)

# =========================
# DB 초기화 (Startup)
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

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if os.path.isdir(TEMPLATE_DIR):
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
        print(f"❌ {path} 로드 실패:", e)

# =========================
# API Routers
# =========================
safe_include("app.routers.items")
safe_include("app.routers.inbound")
safe_include("app.routers.outbound")
safe_include("app.routers.move")
safe_include("app.routers.location")
safe_include("app.routers.inventory")
safe_include("app.routers.history")
safe_include("app.routers.qr_api")
# ⚠️ 엑셀 업로드 안 쓰면 주석 유지
# safe_include("app.routers.upload_inventory")

# =========================
# Page Routers (HTML)
# =========================
safe_include("app.pages.index_page")
safe_include("app.pages.worker_page")
safe_include("app.pages.inbound_page")
safe_include("app.pages.outbound_page")
safe_include("app.pages.move_page")
safe_include("app.pages.inventory_page")
safe_include("app.pages.history_page")
safe_include("app.pages.qr_page")

# 👉 품목 상세 + QR + 작업 연결 (이번에 추가한 핵심)
safe_include("app.pages.item_page")

# =========================
# Health Check
# =========================
@app.get("/ping", summary="서버 상태 확인")
def ping():
    return {"status": "OK"}
