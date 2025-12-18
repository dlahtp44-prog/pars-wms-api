from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db

app = FastAPI(title="PARS WMS")

@app.on_event("startup")
def startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_include(path):
    try:
        m = __import__(path, fromlist=["router"])
        app.include_router(m.router)
    except Exception as e:
        print(path, e)

# Pages
safe_include("app.pages.inbound_page")
safe_include("app.pages.outbound_page")
safe_include("app.pages.move_page")
safe_include("app.pages.inventory_page")
safe_include("app.pages.history_page")
safe_include("app.pages.qr_page")

@app.get("/ping")
def ping():
    return {"status":"OK"}
