from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(
    title="PARS WMS",
    description="입고·출고·이동·재고·작업이력 관리 WMS",
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

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "app/static")),
    name="static"
)

templates = Jinja2Templates(directory="app/templates")

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
def safe_include(path):
    try:
        module = __import__(path, fromlist=["router"])
        app.include_router(module.router)
        print(f"✅ {path} 등록")
    except Exception as e:
        print(f"❌ {path} 실패:", e)

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

# =========================
# Page Routers
# =========================
safe_include("app.pages.index_page")
safe_include("app.pages.worker_page")
safe_include("app.pages.inbound_page")
safe_include("app.pages.outbound_page")
safe_include("app.pages.move_page")
safe_include("app.pages.inventory_page")
safe_include("app.pages.history_page")
safe_include("app.pages.item_page")   # 👈 품번 클릭 상세

# =========================
# Health Check
# =========================
@app.get("/ping")
def ping():
    return {"status": "OK"}
