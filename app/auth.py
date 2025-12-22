from fastapi import Request, HTTPException

USERS = {
    "worker": {"password": "1234", "role": "worker"},
    "admin": {"password": "admin123", "role": "admin"},
}

def login_user(username: str, password: str, request: Request):
    user = USERS.get(username)
    if not user or user["password"] != password:
        raise HTTPException(401, "로그인 실패")

    request.session["user"] = {
        "username": username,
        "role": user["role"]
    }

def require_role(role: str):
    def checker(request: Request):
        user = request.session.get("user")
        if not user or user["role"] != role:
            raise HTTPException(403, "권한 없음")
    return checker
