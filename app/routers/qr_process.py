from fastapi import APIRouter, HTTPException
from app.db import log_qr_error, is_blocked_action
import json

router = APIRouter(prefix="/api/qr", tags=["QR"])

@router.post("/process")
def process_qr(qr_data: str):
    try:
        data = json.loads(qr_data)
        action = data.get("type")

        if action in ("OUT", "MOVE") and is_blocked_action(action):
            raise HTTPException(
                status_code=403,
                detail="QR 오류 누적으로 출고/이동이 차단되었습니다"
            )

        return {"result": "처리 성공", "data": data}

    except Exception as e:
        log_qr_error(qr_data, "CRITICAL", str(e))
        raise HTTPException(status_code=400, detail="QR 처리 실패")
