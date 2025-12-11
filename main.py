from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import inbound, outbound, move, opening, inventory, history, items, location
from app.pages import index, inbound_page, outbound_page, move_page, inventory_page, history_page, admin_page, opening_page

app = FastAPI(title="PARS WMS")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 초기화
init_db()

# static 폴더 연결
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ------------------ API 라우터 등록 ------------------
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(opening.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(items.router)
app.include_router(location.router)

# ------------------ HTML 페이지 라우터 ------------------
app.include_router(index.router)
app.include_router(inbound_page.router)
app.include_router(outbound_page.router)
app.include_router(move_page.router)
app.include_router(inventory_page.router)
app.include_router(history_page.router)
app.include_router(admin_page.router)
app.include_router(opening_page.router)
