# auth.py
import streamlit as st

# -----------------------------
# 🔐 รายชื่อผู้ใช้ (แก้ตามจริง)
# -----------------------------
USERS = {
    "admin": {
        "password": "1234",
        "fullname": "System Admin",
        "role": "admin",
    },
    "demo": {
        "password": "demo1234",
        "fullname": "Demo User",
        "role": "user",
    },
}


def _init_auth_state():
    """เตรียมค่าพื้นฐานใน session_state สำหรับ auth (เรียกทุกครั้งตอน import ได้เลย)"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "display_name" not in st.session_state:
        st.session_state.display_name = None
    if "view" not in st.session_state:
        st.session_state.view = "landing"
    if "current_menu" not in st.session_state:
        st.session_state.current_menu = "หน้าหลัก"


_init_auth_state()


def authenticate_user(username: str, password: str):
    """เช็ค username/password ถ้าถูก return (True, display_name) ถ้าผิด return (False, None)"""
    user = USERS.get(username)
    if not user:
        return False, None

    if password != user["password"]:
        return False, None

    return True, user["fullname"]


def login_user(username: str, display_name: str):
    """เซ็ตสถานะล็อกอิน (จะอยู่ใน session_state จนกว่าจะกด Logout เอง)"""
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.display_name = display_name
    st.session_state.view = "app"


def logout_user():
    """ล้าง session แล้วกลับไปหน้า landing"""
    # ถ้าไม่อยากล้างทุก key ทั้งหมด ก็ล้างเฉพาะที่เกี่ยวกับ auth
    for key in ["logged_in", "username", "display_name", "current_menu"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.logged_in = False
    st.session_state.view = "landing"


def is_logged_in() -> bool:
    """ใช้เช็คทุกครั้ง ก่อนเข้า Dashboard"""
    return bool(st.session_state.get("logged_in", False))
