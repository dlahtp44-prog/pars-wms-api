# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="PARS WMS")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB init
@app.on_event("startup")
def startup():
    from app.db import init_db
    init_db()
    print("✅ DB 초기화 완료")

# static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory="app/static"), name="static")

def safe_include(path: str):
    try:
        module = __import__(path, fromlist=["router"])
        app.include_router(module.router)
        print(f"✅ {path} 등록")
    except Exception as e:
        print(f"❌ {path} 실패:", e)

# pages
safe_include("app.pages.index_page")
safe_include("app.pages.worker_page")
safe_include("app.pages.inbound_page")
safe_include("app.pages.outbound_page")
safe_include("app.pages.move_page")
safe_include("app.pages.inventory_page")
safe_include("app.pages.history_page")
safe_include("app.pages.qr_page")
safe_include("app.pages.item_page")
safe_include("app.pages.upload_page")
safe_include("app.pages.dashboard_page")
safe_include("app.pages.admin_page")

# routers
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

@app.get("/ping")
def ping():
    return {"status": "OK"}
