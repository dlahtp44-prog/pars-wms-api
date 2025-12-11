import os
import sqlite3
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openpyxl import load_workbook

# -----------------------------
# 기본 설정
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "WMS.db")

app = FastAPI()

# 모든 출처 허용 (프론트가 파일이거나 GitHub Pages여도 동작하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# 데이터베이스 연결 함수
# -----------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# 공통 응답 함수
# -----------------------------
def success(message, data=None):
    return {"result": "success", "message": message, "data": data}

def error(message):
    return {"result": "error", "message": message}


# -----------------------------
# API ➊ QR 조회
# -----------------------------
@app.get("/api/scan/{location}")
def scan_location(location: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execut

