# auth.py
"""
ระบบจัดการผู้ใช้สำหรับ MEM System
- เก็บบัญชีผู้ใช้ในไฟล์ users.xlsx (โฟลเดอร์เดียวกับไฟล์ครุภัณฑ์)
- มี default admin: username=admin, password=admin1234
"""

from pathlib import Path
from typing import Tuple

import pandas as pd

from config import DATA_DIR

USERS_FILE = DATA_DIR / "users.xlsx"


def _ensure_users_file():
    """สร้างไฟล์ users.xlsx พร้อม admin เริ่มต้น ถ้ายังไม่มี"""
    if USERS_FILE.exists():
        return

    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        [
            {
                "username": "admin",
                "password": "admin1234",
                "full_name": "System Admin",
                "role": "admin",
            }
        ]
    )
    df.to_excel(USERS_FILE, index=False)


def load_users() -> pd.DataFrame:
    """อ่านตารางบัญชีผู้ใช้จาก users.xlsx"""
    _ensure_users_file()
    try:
        df = pd.read_excel(USERS_FILE)
    except Exception:
        df = pd.DataFrame(columns=["username", "password", "full_name", "role"])

    for col in ["username", "password", "full_name", "role"]:
        if col not in df.columns:
            df[col] = ""

    return df


def save_users(df: pd.DataFrame):
    """บันทึกตารางบัญชีผู้ใช้กลับไปที่ users.xlsx"""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(USERS_FILE, index=False)


def safe_authenticate_admin(username: str, password: str):
    """
    เรียกใช้ authenticate_user จาก auth.py แบบยืดหยุ่น
    รองรับหลายรูปแบบ เช่น
      - True / False
      - (ok,)
      - (ok, display_name)
      - (ok, display_name, role, ...)
    """
    try:
        res = authenticate_user(username, password)
    except Exception:
        # ถ้า auth.py มีปัญหาจริง ๆ (เช่น อ่านไฟล์/ต่อเน็ตไม่ได้) ค่อยเตือน
        if not st.session_state.get("_admin_auth_error_shown", False):
            st.session_state["_admin_auth_error_shown"] = True
            st.warning(
                "ไม่สามารถตรวจสอบสิทธิ์ผ่านระบบผู้ดูแล (auth.py) ได้ "
                "กรุณาตรวจสอบไฟล์ auth.py หรือใช้บัญชีผู้ใช้ที่สมัครในระบบแทน"
            )
        return False, ""

    ok = False
    display_name = username

    # ถ้า auth.py คืนเป็น tuple / list
    if isinstance(res, (tuple, list)):
        if len(res) == 0:
            ok = False
        elif len(res) == 1:
            ok = bool(res[0])
        else:
            # ใช้ตัวแรกเป็นสถานะ, ตัวที่สองเป็นชื่อที่แสดง
            ok = bool(res[0])
            if res[1]:
                display_name = str(res[1])
    else:
        # คืนเป็น bool ตัวเดียว
        ok = bool(res)

    return bool(ok), display_name



def register_user(username: str, password: str, full_name: str) -> Tuple[bool, str]:
    """
    สมัครสมาชิกใหม่ (role จะเป็น 'user' เสมอ)
    คืนค่า: (สำเร็จหรือไม่, ข้อความแจ้ง)
    """
    username = (username or "").strip()
    password = (password or "").strip()
    full_name = (full_name or "").strip()

    if not username or not password:
        return False, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"

    df = load_users()

    # ห้ามซ้ำ username
    if (df["username"].astype(str).str.lower() == username.lower()).any():
        return False, "ชื่อผู้ใช้นี้ถูกใช้แล้ว กรุณาใช้ชื่ออื่น"

    new_row = {
        "username": username,
        "password": password,
        "full_name": full_name or username,
        "role": "user",  # ผู้ใช้ใหม่เป็น user เสมอ
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_users(df)

    return True, "สมัครสมาชิกสำเร็จ สามารถเข้าสู่ระบบได้ทันที"
