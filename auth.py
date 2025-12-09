# auth.py
import streamlit as st

# -------------------------
# กำหนดผู้ใช้ตัวอย่าง (แก้ได้ตามจริง)
# -------------------------
USERS = {
    "admin": {
        "password": "1234",
        "display_name": "System Admin",
    },
    "demo": {
        "password": "demo1234",
        "display_name": "Demo User",
    },
}


def _init_auth_state():
    """เตรียมค่าเริ่มต้นสำหรับ session_state ที่ใช้เรื่องการล็อกอิน
    (ฟังก์ชันนี้จะไม่รีเซ็ตค่า ถ้ามีอยู่แล้ว → ทำให้ refresh แล้วไม่หลุด)
    """
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "display_name" not in st.session_state:
        st.session_state.display_name = None


def authenticate_user(username: str, password: str):
    """ตรวจสอบ username / password

    คืนค่า: (True, display_name) ถ้าถูกต้อง
          : (False, "") ถ้าไม่ถูก
    """
    _init_auth_state()

    user = USERS.get(username)
    if not user:
        return False, ""

    if password != user["password"]:
        return False, ""

    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.display_name = user["display_name"]
    return True, user["display_name"]


def is_authed() -> bool:
    """เช็คว่าตอนนี้ล็อกอินอยู่หรือไม่"""
    _init_auth_state()
    return bool(st.session_state.logged_in)


def logout():
    """ออกจากระบบ (ใช้กับปุ่ม Logout)"""
    _init_auth_state()
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.display_name = None
