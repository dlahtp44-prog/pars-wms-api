# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os

from app.db import init_db

app = FastAPI(
    title="PARS WMS",
    description="입고/출고/이동/재고/이력/QR/대시보드/관리자(롤백)/라벨/엑셀다운",
    version="1.0.0"
)

@app.on_event("startup")
def startup():
    init_db()
    print("✅ DB 초기화 완료")

# static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print("✅ static 마운트:", STATIC_DIR)

# middleware
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
safe_include("app.pages.index_page")           # /
safe_include("app.pages.worker_page")          # /worker
safe_include("app.pages.inbound_page")         # /worker/inbound
safe_include("app.pages.outbound_page")        # /worker/outbound
safe_include("app.pages.move_page")            # /worker/move
safe_include("app.pages.inventory_page")       # /inventory-page
safe_include("app.pages.history_page")         # /history-page
safe_include("app.pages.qr_page")              # /qr-page
safe_include("app.pages.dashboard_page")        # /dashboard
safe_include("app.pages.upload_page")          # /upload
safe_include("app.pages.admin_page")           # /admin
safe_include("app.pages.label_page")           # /labels
safe_include("app.pages.location_view_page")   # /loc

# APIs
safe_include("app.routers.inbound")            # /api/inbound
safe_include("app.routers.outbound")           # /api/outbound
safe_include("app.routers.move")               # /api/move
safe_include("app.routers.inventory")          # /api/inventory
safe_include("app.routers.history")            # /api/history
safe_include("app.routers.qr_api")             # /api/qr-search + /api/location-items
safe_include("app.routers.qr_process")         # /api/qr/process
safe_include("app.routers.upload_inventory")   # /api/upload/inbound
safe_include("app.routers.upload_outbound")    # /api/upload/outbound
safe_include("app.routers.export_excel")       # /api/export/inventory , /api/export/history (CSV)
safe_include("app.routers.qr_generate")        # /api/qr/label/... (외부 QR 이미지 사용)

@app.get("/ping")
def ping():
    return {"status": "OK"}
