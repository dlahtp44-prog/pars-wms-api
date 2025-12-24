from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import init_db
from app.routers import inbound, outbound, inventory, history, move, qr_api, export_excel, admin
from app.pages import index_page, worker_page, inbound_page, outbound_page, inventory_page, history_page, qr_page, dashboard_page, admin_page, location_view_page, label_page, upload_page

app = FastAPI(title="PARS WMS 통합 시스템")

# 1. 서버 시작 시 DB 초기화 실행
init_db()

# 2. 정적 파일 마운트
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 3. API 라우터 등록
app.include_router(inbound.router)
app.include_router(outbound.router)
app.include_router(inventory.router)
app.include_router(history.router)
app.include_router(move.router)
app.include_router(qr_api.router)
app.include_router(export_excel.router)
app.include_router(admin.router)

# 4. 페이지 라우터 등록
app.include_router(index_page.router)
app.include_router(worker_page.router)
app.include_router(inbound_page.router)
app.include_router(outbound_page.router)
app.include_router(inventory_page.router)
app.include_router(history_page.router)
app.include_router(qr_page.router)
app.include_router(dashboard_page.router)
app.include_router(admin_page.router)
app.include_router(location_view_page.router)
app.include_router(label_page.router)
app.include_router(upload_page.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
