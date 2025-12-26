# main.py
# =========================================
# PARS WMS - A안 기준 최종 main.py
# 전체 교체용 (copy & paste 전용)
# =========================================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db


from app.pages.report_page import router as report_page
app.include_router(report_page)


# -----------------------------
# API Routers
# -----------------------------
from app.routers import (
    inbound,
    outbound,
    move,
    inventory,
    history,
    dashboard,
    admin
)

# -----------------------------
# Page Routers
# -----------------------------
from app.pages import (
    index_page,
    inbound_page,
    outbound_page,
    move_page,
    inventory_page,
    history_page,
    dashboard_page,
    admin_page
)

# -----------------------------
# QR Page Routers (import만)
# -----------------------------
from app.pages.qr_move_page import router as qr_move_page
from app.pages.qr_location_page import router as qr_location_page
from app.pages.qr_outbound_page import router as qr_outbound_page


# ==================================================
# APP (여기서 app 생성)
# ==================================================
app = FastAPI(title="PARS WMS")


# ==================================================
# STATIC
# ==================================================
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# ==================================================
# STARTUP
# ==================================================
@app.on_event("startup")
def startup():
    init_db()


# ==================================================
# API ROUTERS
# ==================================================
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(move.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


# ==================================================
# PAGE ROUTERS
# ==================================================
app.include_router(index_page.router)
app.include_router(inbound_page.router)
app.include_router(outbound_page.router)
app.include_router(move_page.router)
app.include_router(inventory_page.router)
app.include_router(history_page.router)
app.include_router(dashboard_page.router)
app.include_router(admin_page.router)

# -----------------------------
# QR PAGES
# -----------------------------
app.include_router(qr_move_page)
app.include_router(qr_location_page)
app.include_router(qr_outbound_page)
