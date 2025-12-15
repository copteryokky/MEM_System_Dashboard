import hashlib
from pathlib import Path
from datetime import datetime

import pandas as pd

from config import DATA_DIR  # ใช้ DATA_DIR ร่วมกับระบบครุภัณฑ์

# -----------------------------
# ค่าคงที่เกี่ยวกับสิทธิ์ผู้ใช้
# -----------------------------
USER_ROLE_ADMIN = "admin"
USER_ROLE_USER = "user"

USERS_FILE_NAME = "users.xlsx"
USERS_FILE = DATA_DIR / USERS_FILE_NAME

# ผู้ใช้ fallback แบบฝังในโค้ด (กันกรณีไฟล์ users.xlsx เสีย)
BUILTIN_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin".encode("utf-8")).hexdigest(),
        "display_name": "System Admin",
        "role": USER_ROLE_ADMIN,
    }
}


def hash_password(password: str) -> str:
    """แปลงรหัสผ่านเป็น hash"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _ensure_users_file():
    """สร้างไฟล์ users.xlsx ถ้ายังไม่มี พร้อมใส่ admin เริ่มต้น"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        admin_row = {
            "username": "admin",
            "password_hash": hash_password("admin"),
            "display_name": "System Admin",
            "role": USER_ROLE_ADMIN,
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        }
        df = pd.DataFrame([admin_row])
        df.to_excel(USERS_FILE, index=False)


def _load_users_df() -> pd.DataFrame:
    """โหลดตารางผู้ใช้จากไฟล์ (ถ้าเสียจะ fallback ใช้ BUILTIN_USERS)"""
    _ensure_users_file()
    try:
        df = pd.read_excel(USERS_FILE)
    except Exception:
        df = pd.DataFrame(
            [
                {
                    "username": u,
                    "password_hash": info["password_hash"],
                    "display_name": info.get("display_name", u),
                    "role": info.get("role", USER_ROLE_ADMIN),
                    "created_at": datetime.utcnow().isoformat(timespec="seconds"),
                }
                for u, info in BUILTIN_USERS.items()
            ]
        )

    expected_cols = ["username", "password_hash", "display_name", "role", "created_at"]
    for col in expected_cols:
        if col not in df.columns:
            if col == "role":
                df[col] = USER_ROLE_USER
            elif col == "created_at":
                df[col] = datetime.utcnow().isoformat(timespec="seconds")
            else:
                df[col] = ""

    # ให้แน่ใจว่ามี admin เสมอ
    mask_admin = df["username"].astype(str).str.lower() == "admin"
    if not mask_admin.any():
        admin_row = {
            "username": "admin",
            "password_hash": hash_password("admin"),
            "display_name": "System Admin",
            "role": USER_ROLE_ADMIN,
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        }
        df = pd.concat([df, pd.DataFrame([admin_row])], ignore_index=True)

    return df[expected_cols]


def _save_users_df(df: pd.DataFrame):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_excel(USERS_FILE, index=False)


def authenticate_user(username: str, password: str):
    """ตรวจสอบ username / password
    คืนค่า (is_valid: bool, display_name: str | None)
    """
    if not username or not password:
        return False, None

    username_norm = str(username).strip()
    if not username_norm:
        return False, None

    df = _load_users_df()
    mask = df["username"].astype(str).str.lower() == username_norm.lower()

    if not mask.any():
        # fallback: กรณีอ่านไฟล์ไม่ได้ / ไม่พบ username ในไฟล์ แต่มีใน BUILTIN_USERS
        user = BUILTIN_USERS.get(username_norm)
        if not user:
            return False, None
        if hash_password(password) != user["password_hash"]:
            return False, None
        return True, user.get("display_name", username_norm)

    user_row = df.loc[mask].iloc[0]
    if hash_password(password) != str(user_row["password_hash"]):
        return False, None

    display_name = str(user_row.get("display_name") or username_norm)
    return True, display_name


def register_user(username: str, password: str, display_name: str | None = None):
    """ลงทะเบียนผู้ใช้ใหม่ (role = user)
    คืนค่า (success: bool, message: str)
    """
    username = (username or "").strip()
    password = (password or "").strip()
    display_name = (display_name or "").strip() or username

    if not username or not password:
        return False, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"

    if " " in username:
        return False, "ชื่อผู้ใช้ห้ามมีเว้นวรรค"

    df = _load_users_df()
    mask = df["username"].astype(str).str.lower() == username.lower()
    if mask.any():
        return False, "มีชื่อผู้ใช้นี้อยู่ในระบบแล้ว"

    new_row = {
        "username": username,
        "password_hash": hash_password(password),
        "display_name": display_name,
        "role": USER_ROLE_USER,
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    _save_users_df(df)
    return True, "สร้างบัญชีผู้ใช้เรียบร้อยแล้ว"


def get_user_display_name(username: str) -> str | None:
    """คืนค่า display_name จาก username (ถ้าไม่มีให้คืน None)
    ใช้สำหรับ restore login จาก query parameter เวลา F5
    """
    if not username:
        return None

    username_norm = str(username).strip()
    df = _load_users_df()
    mask = df["username"].astype(str).str.lower() == username_norm.lower()
    if mask.any():
        row = df.loc[mask].iloc[0]
        return str(row.get("display_name") or username_norm)

    user = BUILTIN_USERS.get(username_norm)
    if not user:
        return None
    return user.get("display_name")


def get_user_role(username: str) -> str | None:
    """คืนค่า role ของผู้ใช้ (admin / user)"""
    if not username:
        return None

    username_norm = str(username).strip()
    df = _load_users_df()
    mask = df["username"].astype(str).str.lower() == username_norm.lower()
    if mask.any():
        row = df.loc[mask].iloc[0]
        role = str(row.get("role") or USER_ROLE_USER)
        return role.lower()

    user = BUILTIN_USERS.get(username_norm)
    if not user:
        return None
    return str(user.get("role", USER_ROLE_ADMIN)).lower()


def is_admin(username: str) -> bool:
    """helper เช็คว่าคือ admin หรือไม่"""
    return get_user_role(username) == USER_ROLE_ADMIN
