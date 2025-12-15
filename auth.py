# auth.py
import pandas as pd
from pathlib import Path
from config import DATA_DIR  # ใช้ DATA_DIR ร่วมกับ app.py

USERS_FILE = DATA_DIR / "users.xlsx"

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "1234"
DEFAULT_ADMIN_DISPLAY = "System Admin"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_users_df() -> pd.DataFrame:
    _ensure_data_dir()
    if not USERS_FILE.exists():
        return pd.DataFrame(columns=["username", "password", "display_name", "role"])

    try:
        df = pd.read_excel(USERS_FILE)
    except Exception:
        return pd.DataFrame(columns=["username", "password", "display_name", "role"])

    for col in ["username", "password", "display_name", "role"]:
        if col not in df.columns:
            df[col] = ""
    return df


def _save_users_df(df: pd.DataFrame):
    _ensure_data_dir()
    df.to_excel(USERS_FILE, index=False)


def authenticate_user(username: str, password: str):
    """
    คืนค่า: (ok: bool, display_name: str | None, role: str | None)
    """
    username = (username or "").strip()
    password = (password or "").strip()

    if not username or not password:
        return False, None, None

    df = _load_users_df()

    if not df.empty:
        mask = df["username"].astype(str).str.lower() == username.lower()
        if mask.any():
            user = df.loc[mask].iloc[0]
            if str(user["password"]) == password:
                display_name = str(user.get("display_name") or username)
                role = str(user.get("role") or "user")
                return True, display_name, role
            else:
                return False, None, None

    # fallback admin เริ่มต้น (กรณีไม่มีใน users.xlsx)
    if username == DEFAULT_ADMIN_USERNAME and password == DEFAULT_ADMIN_PASSWORD:
        return True, DEFAULT_ADMIN_DISPLAY, "admin"

    return False, None, None


def register_user(username: str, password: str, display_name: str = ""):
    """
    สมัครสมาชิกใหม่ → บันทึกลง users.xlsx เป็น role = 'user'
    คืนค่า: (ok: bool, message: str)
    """
    username = (username or "").strip()
    password = (password or "").strip()
    display_name = (display_name or "").strip()

    if not username or not password:
        return False, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"

    df = _load_users_df()

    if not df.empty:
        if (df["username"].astype(str).str.lower() == username.lower()).any():
            return False, "มีชื่อผู้ใช้นี้อยู่ในระบบแล้ว"

    if not display_name:
        display_name = username

    new_row = pd.DataFrame(
        [
            {
                "username": username,
                "password": password,
                "display_name": display_name,
                "role": "user",
            }
        ]
    )

    df = pd.concat([df, new_row], ignore_index=True)
    _save_users_df(df)

    return True, "สมัครสมาชิกสำเร็จแล้ว สามารถเข้าสู่ระบบได้ทันที"
