from fastapi import FastAPI
from db import Base, engine

app = FastAPI()

# DB 테이블 자동 생성
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"msg": "pars-wms server OK (DB connected)"}

