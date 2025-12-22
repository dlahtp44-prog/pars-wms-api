from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="PARS WMS")

@app.on_event("startup")
def startup():
    from app.db import init_db
    init_db()
    print("✅ DB 초기화 완료")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE_DIR, "app")
STATIC_DIR = os.path.join(APP_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_include(path: str):
    try:
        module = __import__(path, fromlist=["router"])
        app.include_router(module.router)
        print(f"✅ {path} 등록")
    except Exception as e:
        print(f"❌ {path} 실패:", e)

# Pages
safe_include("app.pages.index_page")        # /
safe_include("app.pages.worker_page")       # /worker
safe_include("app.pages.inbound_page")      # /worker/inbound
safe_include("app.pages.outbound_page")     # /worker/outbound
safe_include("app.pages.move_page")         # /worker/move
safe_include("app.pages.inventory_page")    # /inventory-page
safe_include("app.pages.history_page")      # /history-page
safe_include("app.pages.qr_page")           # /qr-page
safe_include("app.pages.item_page")         # /item/{item_code}
safe_include("app.pages.upload_page")       # /upload-page
safe_include("app.pages.admin_page")        # /admin-page
safe_include("app.pages.dashboard_page")



# APIs
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
