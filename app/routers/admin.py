from fastapi import APIRouter, HTTPException
from app import db

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/logs")
async def get_logs():
    conn = db.get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(log) for log in logs]

@router.post("/rollback/{log_id}")
async def rollback(log_id: int):
    success = db.process_rollback(log_id)
    if not success:
        raise HTTPException(status_code=400, detail="롤백에 실패했습니다.")
    return {"message": "정상적으로 롤백되었습니다."}
