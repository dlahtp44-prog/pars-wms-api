import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Render에서 환경변수 DATABASE_URL을 읽음
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL 환경변수가 설정되지 않았습니다!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


