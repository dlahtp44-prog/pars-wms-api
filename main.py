from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
import importlib

# db.py와 admin.py 임포트
from app.db import init_db
from app.routers import admin

app = FastAPI(title="PARS WMS", version="1.0.0")

# 서버 시작 시 DB 초기화 (6개 항목 및 롤백 테이블 생성)
@app.on_event("startup")
def startup():
    init_db()
    print("✅ 데이터베이스 및 테이블 초기화 완료")

# 정적 파일 마운트 (CSS, JS, Images)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print("✅ static 마운트 완료:", STATIC_DIR)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 설정 (itsdangerous 라이브러리 필요)
SECRET_KEY = os.getenv("SECRET_KEY", "pars-wms-secret-key-1224")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 루터 자동 등록 함수 (오류 추적 기능 강화)
def safe_include(path: str):
    try:
        # 동적 임포트
        module = importlib.import_module(path)
        if hasattr(module, "router"):
            app.include_router(module.router)
            print(f"✅ {path} 등록 성공")
        else:
            print(f"⚠️ {path} 실패: 'router' 객체를 찾을 수 없음")
    except Exception as e:
        print(f"❌ {path} 에러 발생: {e}")

# --- [1. Pages 등록] ---
print("\n--- 페이지 로딩 중 ---")
safe_include("app.pages.index_page")
safe_include("app.pages.worker_page")
safe_include("app.pages.inbound_page")
safe_include("app.pages.outbound_page")
safe_include("app.pages.inventory_page")
safe_include("app.pages.history_page")
safe_include("app.pages.qr_page")
safe_include("app.pages.dashboard_page")
safe_include("app.pages.admin_page")
safe_include("app.pages.location_view_page")
safe_include("app.pages.label_page")
safe_include("app.pages.upload_page")

# --- [2. APIs 등록] ---
print("\n--- API 로딩 중 ---")
safe_include("app.routers.inbound")
safe_include("app.routers.outbound")
safe_include("app.routers.move")
safe_include("app.routers.inventory")
safe_include("app.routers.history")
safe_include("app.routers.qr_api")
safe_include("app.routers.export_excel")

# 관리자 전용 루터 별도 등록
try:
    app.include_router(admin.router)
    print("✅ app.routers.admin 등록 성공")
except Exception as e:
    print(f"❌ app.routers.admin 실패: {e}")

@app.get("/ping")
def ping():
    return {"status": "WMS Server Running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
