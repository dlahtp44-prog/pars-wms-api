from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from app.db import init_db

app = FastAPI(
    title="PARS WMS",
    description="입고/출고/이동/재고/이력/QR/대시보드/관리자(롤백)",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()
    print("✅ DB 초기화 완료")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print("✅ static 마운트:", STATIC_DIR)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY", "pars-wms-secret-key-change-me")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

def safe_include(path: str):
    try:
        m = __import__(path, fromlist=["router"])
        app.include_router(m.router)
        print(f"✅ {path} 등록")
    except Exception as e:
        print(f"❌ {path} 실패:", e)

# Pages
safe_include("app.pages.index_page")
safe_include("app.pages.worker_page")
safe_include("app.pages.inbound_page")
safe_include("app.pages.outbound_page")
safe_include("app.pages.move_page")
safe_include("app.pages.inventory_page")
safe_include("app.pages.history_page")
safe_include("app.pages.qr_page")
safe_include("app.pages.dashboard_page")
safe_include("app.pages.admin_page")
safe_include("app.pages.upload_page")
safe_include("app.pages.item_page")

# APIs
safe_include("app.routers.inbound")
safe_include("app.routers.outbound")
safe_include("app.routers.move")
safe_include("app.routers.inventory")
safe_include("app.routers.history")
safe_include("app.routers.qr_process")
safe_include("app.routers.qr_api")
safe_include("app.routers.upload_inventory")
safe_include("app.routers.upload_outbound")

@app.get("/ping")
def ping():
    return {"status": "OK"}
