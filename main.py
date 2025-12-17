from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="PARS WMS",
    description="물류 입·출고 및 재고 관리를 위한 WMS API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.routers.items import router as items_router
from app.routers.inbound import router as inbound_router
from app.routers.outbound import router as outbound_router
from app.routers.move import router as move_router
from app.routers.location import router as location_router
from app.routers.inventory import router as inventory_router
from app.routers.history import router as history_router
from app.routers.qr_api import router as qr_router

from app.pages.index_page import router as index_router
from app.pages.qr_page import router as qr_page_router

app.include_router(index_router)
app.include_router(items_router)
app.include_router(inbound_router)
app.include_router(outbound_router)
app.include_router(move_router)
app.include_router(location_router)
app.include_router(inventory_router)
app.include_router(history_router)
app.include_router(qr_router)
app.include_router(qr_page_router)

@app.get(
    "/ping",
    summary="서버 상태 확인",
    description="서버가 정상 동작 중인지 확인합니다."
)
def ping():
    return {"상태": "정상"}
