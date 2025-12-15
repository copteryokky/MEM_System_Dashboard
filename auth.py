import streamlit as st
import pandas as pd
from pathlib import Path

from config import DATA_DIR  # ใช้โฟลเดอร์เดียวกับไฟล์ Excel อื่น ๆ

# -----------------------------
# CONFIG สำหรับเก็บข้อมูลผู้ใช้
# -----------------------------
USERS_FILE = DATA_DIR / "users.xlsx"

# โครงสร้างคอลัมน์ในไฟล์ผู้ใช้
USER_COLS = ["username", "password", "display_name", "role"]


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _init_default_admin(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    ถ้ายังไม่มีไฟล์ / ไม่มี admin เลย → สร้าง admin เริ่มต้นให้
    username: admin
    password: admin123
    role: admin
    """
    if df is None or df.empty:
        df = pd.DataFrame(columns=USER_COLS)

    if "username" not in df.columns:
        df = pd.DataFrame(columns=USER_COLS)

    has_admin = False
    try:
        has_admin = (df["role"] == "admin").any()
    except Exception:
        has_admin = False

    if not has_admin:
        admin_row = {
            "username": "admin",
            "password": "admin123",
            "display_name": "ผู้ดูแลระบบ (เริ่มต้น)",
            "role": "admin",
        }
        df = pd.concat([df, pd.DataFrame([admin_row])], ignore_index=True)

    # ให้แน่ใจว่ามีคอลัมน์ครบ
    for c in USER_COLS:
        if c not in df.columns:
            df[c] = ""

    return df[USER_COLS]


def _load_users() -> pd.DataFrame:
    """โหลดข้อมูลผู้ใช้จาก Excel ถ้าไม่มีไฟล์จะสร้าง admin เริ่มต้นให้"""
    _ensure_data_dir()

    if not USERS_FILE.exists():
        # ยังไม่มีไฟล์เลย → สร้าง admin เริ่มต้น
        df = _init_default_admin(pd.DataFrame(columns=USER_COLS))
        df.to_excel(USERS_FILE, index=False)
        return df

    try:
        df = pd.read_excel(USERS_FILE)
    except Exception:
        df = pd.DataFrame(columns=USER_COLS)

    df = _init_default_admin(df)
    return df


def _save_users(df: pd.DataFrame):
    """บันทึกข้อมูลผู้ใช้ลง Excel"""
    _ensure_data_dir()
    df = df[USER_COLS].copy()
    df.to_excel(USERS_FILE, index=False)


# =========================
# ฟังก์ชันหลักที่ app.py เรียกใช้
# =========================
def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """
    ตรวจสอบ username / password
    คืนค่า (สำเร็จหรือไม่, display_name)
    ถ้าสำเร็จจะตั้งค่า role ใน session_state ด้วย
    """
    df = _load_users()

    if "username" not in df.columns or "password" not in df.columns:
        return False, ""

    mask = (df["username"].astype(str) == str(username)) & (
        df["password"].astype(str) == str(password)
    )
    if not mask.any():
        return False, ""

    row = df[mask].iloc[0]
    display_name = str(row.get("display_name", username) or username)
    role = str(row.get("role", "user") or "user")

    # เก็บไว้ใน session_state (ให้ app.py ใช้ต่อ)
    st.session_state["current_role"] = role
    st.session_state["username"] = username
    st.session_state["display_name"] = display_name

    return True, display_name


def register_user(username: str, password: str, display_name: str) -> tuple[bool, str]:
    """
    สมัครสมาชิกใหม่ → role เป็น user
    ถ้า username ซ้ำจะสมัครไม่ได้
    """
    username = str(username).strip()
    password = str(password).strip()
    display_name = str(display_name).strip()

    if not username or not password or not display_name:
        return False, "กรุณากรอกข้อมูลให้ครบทุกช่อง"

    df = _load_users()

    if (df["username"].astype(str) == username).any():
        return False, "มีชื่อผู้ใช้นี้ในระบบแล้ว กรุณาใช้ชื่ออื่น"

    new_row = {
        "username": username,
        "password": password,
        "display_name": display_name,
        "role": "user",  # สมาชิกที่สมัครเองให้เป็น user ทั่วไป
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    _save_users(df)

    return True, "สมัครสมาชิกเรียบร้อยแล้ว"


def get_current_user_role() -> str:
    """
    คืนค่า role ปัจจุบันจาก session_state (ถ้าไม่มีให้ถือเป็น user)
    app.py จะเอาไปเซ็ต query params ด้วยเพื่อกันหลุดตอน F5
    """
    # ถ้าใน session มีอยู่แล้วก็ใช้เลย
    role = st.session_state.get("current_role")
    if role:
        return str(role)

    # ถ้าไม่มี แต่มี username ใน session ให้ลองโหลดจากไฟล์
    username = st.session_state.get("username")
    if username:
        df = _load_users()
        mask = df["username"].astype(str) == str(username)
        if mask.any():
            row = df[mask].iloc[0]
            role = str(row.get("role", "user") or "user")
            st.session_state["current_role"] = role
            return role

    # ถ้าไม่รู้อะไรเลย → default เป็น user
    return "user"


def is_admin() -> bool:
    """เช็คว่า user ปัจจุบันเป็น admin หรือไม่"""
    return get_current_user_role() == "admin"
