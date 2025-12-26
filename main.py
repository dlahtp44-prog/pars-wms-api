# main.py
# =========================================
# PARS WMS - A안 기준 최종 main.py
# 전체 교체용 (copy & paste 전용)
# =========================================

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db

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
# QR Page Router
# -----------------------------
from app.pages.qr_move_page import router as qr_move_page


# ==================================================
# APP
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
@app.on_event("star_
