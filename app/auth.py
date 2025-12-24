from fastapi import Request, HTTPException

def require_admin(request: Request):
    if request.session.get("is_admin") is True:
        return True
    raise HTTPException(status_code=401, detail="관리자 로그인 필요")
