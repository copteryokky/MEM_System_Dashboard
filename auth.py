# auth.py
import streamlit as st
import pandas as pd
from pathlib import Path

from config import DATA_DIR  # ใช้ DATA_DIR จาก config.py

# -----------------------------
# ตั้งค่าไฟล์เก็บผู้ใช้
# -----------------------------
USERS_FILE = DATA_DIR / "users.xlsx"


def _init_users_file():
    """
    ถ้ายังไม่มีไฟล์ users.xlsx ให้สร้างไฟล์ใหม่
    พร้อมแอดมินเริ่มต้น 1 คน: username=admin, password=1234, role=admin
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if USERS_FILE.exists():
        return

    df = pd.DataFrame(
        [
            {
                "username": "admin",
                "password": "1234",
                "display_name": "System Admin",
                "role": "admin",
            }
        ]
    )
    df.to_excel(USERS_FILE, index=False)


def _load_users_df() -> pd.DataFrame:
    """อ่านข้อมูลผู้ใช้จาก users.xlsx"""
    _init_users_file()

    try:
        df = pd.read_excel(USERS_FILE).fillna("")
    except Exception:
        # ถ้าอ่านไม่ได้ให้สร้างใหม่
        df = pd.DataFrame(
            [
                {
                    "username": "admin",
                    "password": "1234",
                    "display_name": "System Admin",
                    "role": "admin",
                }
            ]
        )
        df.to_excel(USERS_FILE, index=False)

    # กันกรณีหัวคอลัมน์ไม่ครบ
    for col in ["username", "password", "display_name", "role"]:
        if col not in df.columns:
            df[col] = ""

    return df


def _save_users_df(df: pd.DataFrame):
    """บันทึกกลับลง users.xlsx"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_excel(USERS_FILE, index=False)


# -----------------------------
# ฟังก์ชันใช้ใน app.py
# -----------------------------
def authenticate_user(username: str, password: str):
    """
    ใช้ตอนล็อกอิน
    คืนค่า (True, display_name) ถ้าถูกต้อง
          (False, "") ถ้าผิด
    """
    df = _load_users_df()

    row = df[(df["username"] == username) & (df["password"] == password)]
    if row.empty:
        return False, ""

    row = row.iloc[0]
    display_name = str(row.get("display_name") or username)
    role = str(row.get("role") or "user")

    # เก็บลง session_state ให้หน้าอื่นใช้
    st.session_state["current_username"] = username
    st.session_state["current_display_name"] = display_name
    st.session_state["current_role"] = role

    return True, display_name


def register_user(username: str, password: str, display_name: str):
    """
    สมัครสมาชิกใหม่ (user ทั่วไป)
    คืนค่า (True, msg) ถ้าสำเร็จ
          (False, msg) ถ้ามีปัญหา เช่น ชื่อซ้ำ
    """
    username = (username or "").strip()
    password = (password or "").strip()
    display_name = (display_name or "").strip()

    if not username or not password:
        return False, "กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบ"

    df = _load_users_df()

    # กันชื่อซ้ำ
    if (df["username"] == username).any():
        return False, "มีชื่อผู้ใช้งานนี้อยู่ในระบบแล้ว"

    if not display_name:
        display_name = username

    new_row = {
        "username": username,
        "password": password,
        "display_name": display_name,
        "role": "user",  # ผู้ใช้ใหม่ให้สิทธิ์เป็น user ทั่วไป
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    _save_users_df(df)

    return True, "สมัครสมาชิกสำเร็จ"


def get_current_user_role() -> str:
    """
    ใช้ดู role ของคนที่ล็อกอินอยู่ตอนนี้
    (admin / user)
    """
    # ถ้ายังไม่เคยเซ็ต ให้ถือว่าเป็น user ทั่วไป
    return st.session_state.get("current_role", "user")


def is_admin() -> bool:
    """เช็คว่า user ปัจจุบันเป็น admin หรือไม่"""
    return get_current_user_role() == "admin"
