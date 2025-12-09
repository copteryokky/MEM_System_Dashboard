import hashlib

# ตัวอย่าง user 1 คน (admin / admin)
USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin".encode("utf-8")).hexdigest(),
        "display_name": "System Admin",
    }
}


def authenticate_user(username: str, password: str):
    """ตรวจสอบ username / password

    คืนค่า (is_valid: bool, display_name: str | None)
    """
    if not username or not password:
        return False, None

    user = USERS.get(username)
    if not user:
        return False, None

    pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if pwd_hash != user["password_hash"]:
        return False, None

    return True, user["display_name"]


def get_user_display_name(username: str) -> str | None:
    """คืนค่า display_name จาก username (ถ้าไม่มีให้คืน None)

    ใช้สำหรับ restore การล็อกอินจาก query parameter เวลาผู้ใช้กด F5
    """
    user = USERS.get(username)
    if not user:
        return None
    return user.get("display_name")
