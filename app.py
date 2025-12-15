import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import streamlit as st
import altair as alt

# ==========================
# CONFIG พื้นฐาน / PATH ต่าง ๆ
# ==========================

try:
    # ถ้าคุณมีไฟล์ config.py อยู่แล้วจะใช้ค่าจากตรงนั้น
    from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH  # type: ignore
except Exception:
    # fallback เผื่อไม่มี config.py
    DATA_DIR = Path("data")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_EXCEL_NAME = "Smart.xlsx"
    DEFAULT_EXCEL_PATH = DATA_DIR / DEFAULT_EXCEL_NAME

ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"

# คอลัมน์สำหรับระบบแจ้งซ่อม / หมายเหตุ
MAINT_STATUS_COL = "สถานะแจ้งซ่อม"
MAINT_REQUEST_DATE_COL = "วันที่แจ้งซ่อมล่าสุด"
MAINT_DUE_DATE_COL = "กำหนดซ่อมเสร็จ"
MAINT_EST_DAYS_COL = "คาดว่าซ่อมใช้เวลากี่วัน"
MAINT_RESULT_COL = "ผลการซ่อม/การประเมินสภาพ"
MAINT_NOTE_COL = "หมายเหตุการซ่อม/บำรุงรักษา"
USER_NOTE_COL = "หมายเหตุจากผู้ใช้งาน"

MAINT_STATUS_CHOICES = [
    "ยังไม่เคยแจ้งซ่อม",
    "แจ้งซ่อมแล้ว - กำลังดำเนินการ",
    "ซ่อมเสร็จแล้ว",
    "ปลดระวาง / รอจำหน่าย",
]

MAINT_RESULT_CHOICES = [
    "",
    "ซ่อมเสร็จ ใช้งานได้ปกติ",
    "ซ่อมแล้ว แต่มีข้อจำกัด",
    "ซ่อมไม่ได้ / จำหน่าย",
]

# ไฟล์เก็บผู้ใช้
USERS_PATH = DATA_DIR / "mem_users.xlsx"


# ==========================
# STYLE
# ==========================

def set_login_style() -> None:
    st.set_page_config(
        page_title="MEM System – Login",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        /* ซ่อน sidebar ช่วงหน้า Login */
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        body {
            background: radial-gradient(circle at top, #E3F2FD 0, #e9f0ff 40%, #dfe7ff 70%, #cfd8ff 100%);
        }

        .mem-login-wrapper {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: "Sarabun", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .mem-login-card {
            width: 420px;
            max-width: 94vw;
            background: rgba(255, 255, 255, 0.94);
            border-radius: 28px;
            box-shadow:
                0 24px 60px rgba(15, 23, 42, 0.18),
                0 0 0 1px rgba(148, 163, 184, 0.35);
            padding: 28px 26px 24px;
            backdrop-filter: blur(18px);
        }

        .mem-login-title {
            font-size: 1.45rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
        }

        .mem-login-subtitle {
            font-size: 0.9rem;
            color: #64748B;
            margin-bottom: 20px;
        }

        .mem-login-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(59, 130, 246, 0.08);
            color: #1D4ED8;
            font-size: 0.8rem;
            margin-bottom: 12px;
        }

        .mem-login-pill-dot {
            width: 6px;
            height: 6px;
            border-radius: 999px;
            background: #22C55E;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            border-radius: 999px;
            padding: 4px;
            background: #EEF2FF;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 0.85rem;
        }

        .stTextInput > div > div > input,
        .stPasswordInput > div > div > input {
            border-radius: 999px;
        }

        .stButton>button {
            width: 100%;
            border-radius: 999px;
            background: linear-gradient(135deg, #2563EB, #4F46E5);
            border: none;
            color: #fff;
            font-weight: 600;
            padding: 0.55rem 0;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.38);
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #1D4ED8, #4338CA);
        }

        .mem-login-footnote {
            font-size: 0.78rem;
            color: #94A3B8;
            margin-top: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_main_style() -> None:
    st.set_page_config(
        page_title="MEM System – Medical Equipment Management",
        page_icon="🩺",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        body {
            background: #EFF3FB;
        }

        /* แสดง sidebar หลังจากล็อกอิน */
        section[data-testid="stSidebar"] {
            display: flex !important;
        }

        /* Sidebar custom */
        section[data-testid="stSidebar"] {
            background: #020617;
        }
        section[data-testid="stSidebar"] > div {
            background: #020617;
        }

        .mem-sidebar-user-card {
            background: radial-gradient(circle at top left, #1D4ED8 0, #020617 55%);
            border-radius: 22px;
            padding: 18px 16px;
            color: #E5E7EB;
            margin-bottom: 18px;
            box-shadow:
                0 18px 40px rgba(15, 23, 42, 0.75),
                0 0 0 1px rgba(148, 163, 184, 0.26);
        }
        .mem-sidebar-user-avatar {
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: radial-gradient(circle at 30% 10%, #FBBF24 0, #FB7185 40%, #6366F1 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.1rem;
            color: white;
            margin-bottom: 8px;
        }
        .mem-sidebar-user-name {
            font-size: 0.9rem;
            font-weight: 600;
        }
        .mem-sidebar-user-role {
            font-size: 0.78rem;
            color: #CBD5F5;
        }
        .mem-sidebar-user-status {
            font-size: 0.72rem;
            margin-top: 4px;
            color: #A5B4FC;
        }

        .mem-menu-title {
            font-size: 0.8rem;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: #64748B;
            margin: 10px 2px 6px;
        }

        .mem-menu-btn, .mem-menu-btn-active {
            margin-bottom: 8px;
        }
        .mem-menu-btn button, .mem-menu-btn-active button {
            width: 100%;
            border-radius: 999px;
            padding: 0.4rem 0.2rem;
            font-size: 0.85rem;
            border: 1px solid rgba(148, 163, 184, 0.4);
            background: rgba(15, 23, 42, 0.96);
            color: #E5E7EB;
        }
        .mem-menu-btn-active button {
            background: linear-gradient(135deg, #2563EB, #4F46E5);
            border-color: transparent;
            box-shadow: 0 10px 26px rgba(37, 99, 235, 0.55);
        }
        .mem-logout-btn button {
            width: 100%;
            border-radius: 999px;
            padding: 0.4rem 0.2rem;
            font-size: 0.85rem;
            border: none;
            margin-top: 16px;
            background: #EF4444;
            color: white;
        }
        .mem-logout-btn button:hover {
            background: #DC2626;
        }

        /* ส่วนเนื้อหา */
        .mem-page-container {
            padding: 16px 10px 40px;
        }
        .mem-page-header {
            margin-bottom: 8px;
        }
        .mem-page-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: #0F172A;
        }
        .mem-page-subtitle {
            font-size: 0.86rem;
            color: #6B7280;
        }

        .mem-stat-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 18px;
        }
        .mem-stat-card {
            background: white;
            border-radius: 18px;
            padding: 10px 12px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            border: 1px solid rgba(148, 163, 184, 0.22);
        }
        .mem-stat-label {
            font-size: 0.8rem;
            color: #6B7280;
        }
        .mem-stat-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: #111827;
        }
        .mem-stat-pill {
            font-size: 0.7rem;
            color: #4B5563;
            padding: 2px 8px;
            border-radius: 999px;
            background: #F3F4FF;
            display: inline-block;
            margin-top: 4px;
        }

        .mem-card {
            background: white;
            border-radius: 22px;
            padding: 16px 18px 18px;
            box-shadow:
                0 18px 45px rgba(15, 23, 42, 0.06),
                0 0 0 1px rgba(148, 163, 184, 0.22);
            margin-bottom: 16px;
        }
        .mem-card-title {
            font-weight: 600;
            color: #111827;
            margin-bottom: 4px;
        }
        .mem-card-subtitle {
            font-size: 0.8rem;
            color: #6B7280;
            margin-bottom: 12px;
        }

        /* calendar */
        .mem-cal-wrapper {
            background: white;
            border-radius: 22px;
            padding: 16px 18px 10px;
            box-shadow:
                0 18px 45px rgba(15, 23, 42, 0.06),
                0 0 0 1px rgba(148, 163, 184, 0.16);
            margin-bottom: 16px;
        }
        .mem-cal-header {
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .mem-cal-sub {
            font-size: 0.78rem;
            color: #6B7280;
            margin-bottom: 10px;
        }
        .mem-cal-months {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
        }
        .mem-cal-month-card {
            background: #F9FAFB;
            border-radius: 18px;
            padding: 10px 12px 8px;
            box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.25);
        }
        .mem-cal-month-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: #111827;
            margin-bottom: 4px;
        }
        .mem-cal-grid {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: 2px;
        }
        .mem-cal-day-header {
            text-align: center;
            font-size: 0.7rem;
            padding: 2px 0;
            color: #9CA3AF;
        }
        .mem-cal-day {
            text-align: center;
            font-size: 0.72rem;
            padding: 4px 0;
            border-radius: 999px;
            color: #4B5563;
        }
        .mem-cal-day.has-event {
            background: #DBEAFE;
            font-weight: 600;
            color: #1D4ED8;
        }

        /* cards แผนสอบเทียบ */
        .cal-equip-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-height: 420px;
            overflow-y: auto;
        }
        .cal-equip-card {
            background: white;
            border-radius: 18px;
            padding: 10px 12px;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
            border-left: 3px solid #4F46E5;
        }
        .cal-equip-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #111827;
            margin-bottom: 2px;
        }
        .cal-equip-meta {
            font-size: 0.76rem;
            color: #6B7280;
        }
        .cal-equip-note {
            font-size: 0.76rem;
            color: #4B5563;
            margin-top: 2px;
        }

        /* ฟอร์มรายละเอียดครุภัณฑ์ */
        .mem-asset-header {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 4px;
            color: #111827;
        }
        .mem-asset-sub {
            font-size: 0.8rem;
            color: #6B7280;
            margin-bottom: 8px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================
# AUTH & USERS
# ==========================

def _ensure_users_file(df: pd.DataFrame) -> pd.DataFrame:
    # สร้าง admin เริ่มต้นถ้ายังไม่มี
    if "username" not in df.columns:
        df["username"] = []
    if "password" not in df.columns:
        df["password"] = []
    if "full_name" not in df.columns:
        df["full_name"] = []
    if "role" not in df.columns:
        df["role"] = []

    has_admin = False
    if not df.empty:
        has_admin = ((df["role"].astype(str) == "admin")).any()

    if not has_admin:
        import hashlib
        admin_row = {
            "username": "admin",
            "password": hashlib.sha256("admin1234".encode("utf-8")).hexdigest(),
            "full_name": "System Admin",
            "role": "admin",
        }
        df = pd.concat([df, pd.DataFrame([admin_row])], ignore_index=True)
        df.to_excel(USERS_PATH, index=False)
    return df


def load_users() -> pd.DataFrame:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if USERS_PATH.exists():
        try:
            df = pd.read_excel(USERS_PATH)
        except Exception:
            df = pd.DataFrame(columns=["username", "password", "full_name", "role"])
    else:
        df = pd.DataFrame(columns=["username", "password", "full_name", "role"])
    return _ensure_users_file(df)


def save_users(df: pd.DataFrame) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(USERS_PATH, index=False)


def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def auth_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    df = load_users()
    if df.empty:
        return None
    username = username.strip()
    if not username:
        return None

    # เปรียบเทียบ username แบบ case-insensitive
    mask = df["username"].astype(str).str.lower() == username.lower()
    if not mask.any():
        return None

    row = df[mask].iloc[0]
    pwd_hash = hash_password(password)
    if str(row.get("password", "")) != pwd_hash:
        return None

    return {
        "username": str(row.get("username", "")),
        "full_name": str(row.get("full_name", "")) or str(row.get("username", "")),
        "role": str(row.get("role", "")) or "user",
    }


def auth_register(username: str, full_name: str, password: str, password2: str) -> str:
    username = username.strip()
    full_name = full_name.strip()

    if not username or not password or not password2:
        return "กรุณากรอกข้อมูลให้ครบถ้วน"
    if password != password2:
        return "รหัสผ่านทั้งสองช่องไม่ตรงกัน"

    df = load_users()
    if not df.empty:
        if (df["username"].astype(str).str.lower() == username.lower()).any():
            return "มีชื่อผู้ใช้นี้อยู่ในระบบแล้ว"

    new_row = {
        "username": username,
        "full_name": full_name or username,
        "password": hash_password(password),
        "role": "user",  # สมัครใหม่เป็น user เสมอ
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_users(df)
    return "success"


# ==========================
# Excel Helper – ครุภัณฑ์
# ==========================

def get_current_excel_path() -> Path:
    # ตอนนี้ใช้ DEFAULT_EXCEL_PATH เป็นหลัก
    return Path(DEFAULT_EXCEL_PATH)


def load_equipment_data() -> pd.DataFrame:
    path = get_current_excel_path()
    if not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)
    except Exception:
        return pd.DataFrame()

    # เติมคอลัมน์ที่จำเป็นถ้ายังไม่มี
    for col in [
        MAINT_STATUS_COL,
        MAINT_REQUEST_DATE_COL,
        MAINT_DUE_DATE_COL,
        MAINT_EST_DAYS_COL,
        MAINT_RESULT_COL,
        MAINT_NOTE_COL,
        USER_NOTE_COL,
    ]:
        if col not in df.columns:
            df[col] = ""

    # ถ้ายังไม่มีสถานะให้กำหนด default
    df[MAINT_STATUS_COL] = df[MAINT_STATUS_COL].replace("", MAINT_STATUS_CHOICES[0])

    return df


def save_equipment_data(df: pd.DataFrame) -> None:
    path = get_current_excel_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


# ==========================
# Utility – column & query params
# ==========================

def find_name_column(df: pd.DataFrame) -> Optional[str]:
    if df.empty:
        return None
    cols = [str(c) for c in df.columns]
    # หา column ที่มีคำว่า "ชื่อ" ก่อน
    for c in cols:
        if "ชื่อ" in c and ("เครื่อง" in c or "ครุภัณฑ์" in c or "อุปกรณ์" in c):
            return c
    for c in cols:
        if "ชื่อ" in c:
            return c
    # fallback เป็น column แรกที่ไม่ใช่รหัส
    for c in cols:
        if c != ASSET_CODE_COL:
            return c
    return cols[0]


def get_query_param(name: str, default: Optional[str] = None) -> Optional[str]:
    # รองรับทั้งเวอร์ชันใหม่/เก่าของ streamlit
    try:
        params = st.query_params  # type: ignore[attr-defined]
        if name in params:
            return str(params[name])
    except Exception:
        try:
            params = st.experimental_get_query_params()
            if name in params and params[name]:
                return str(params[name][0])
        except Exception:
            pass
    return default


# ==========================
# UI Components – ส่วนย่อย
# ==========================

def render_auth_page() -> None:
    set_login_style()

    with st.container():
        st.markdown('<div class="mem-login-wrapper"><div class="mem-login-card">', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="mem-login-pill">
              <span class="mem-login-pill-dot"></span>
              MEM System – Medical Equipment
            </div>
            <div class="mem-login-title">เข้าสู่ระบบใช้งาน MEM System</div>
            <div class="mem-login-subtitle">
              ระบบจัดการครุภัณฑ์ เครื่องมือแพทย์ การแจ้งซ่อม และแผนสอบเทียบแบบครบวงจร<br/>
              <strong>admin / admin1234</strong> คือบัญชีเริ่มต้น (เปลี่ยนรหัสผ่านภายหลังได้)
            </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิกใหม่"])

        with tab_login:
            username = st.text_input("ชื่อผู้ใช้ (Username)", key="login_username")
            password = st.text_input("รหัสผ่าน (Password)", type="password", key="login_password")

            if st.button("เข้าสู่ระบบ", key="btn_login"):
                user = auth_login(username, password)
                if not user:
                    st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                else:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user
                    # หน้าแรกหลังล็อกอิน
                    st.session_state.active_page = "dashboard"
                    st.experimental_rerun()

        with tab_register:
            new_username = st.text_input("ชื่อผู้ใช้ (Username)", key="reg_username")
            full_name = st.text_input("ชื่อ-นามสกุล หรือชื่อที่ใช้แสดง", key="reg_fullname")
            pw1 = st.text_input("รหัสผ่าน", type="password", key="reg_pw1")
            pw2 = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_pw2")

            if st.button("สมัครสมาชิก", key="btn_register"):
                msg = auth_register(new_username, full_name, pw1, pw2)
                if msg == "success":
                    st.success("สมัครสมาชิกสำเร็จ สามารถเข้าสู่ระบบได้เลยด้วยบัญชีที่สร้าง")
                else:
                    st.error(msg)

        st.markdown(
            """
            <div class="mem-login-footnote">
              ระบบจะจดจำสถานะการล็อกอินของคุณใน session เดียวกัน<br/>
              หากปิดเบราว์เซอร์ทั้งหมดแล้วกลับมาใหม่ จะต้องเข้าสู่ระบบอีกครั้ง
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div></div>", unsafe_allow_html=True)


def sidebar_nav() -> None:
    user = st.session_state.get("current_user", {}) or {}
    role = user.get("role", "user")
    full_name = user.get("full_name", "ผู้ใช้งาน")
    username = user.get("username", "")

    with st.sidebar:
        st.markdown(
            f"""
            <div class="mem-sidebar-user-card">
              <div class="mem-sidebar-user-avatar">{(username[:2] or "ME").upper()}</div>
              <div class="mem-sidebar-user-name">{full_name}</div>
              <div class="mem-sidebar-user-role">{'ผู้ดูแลระบบ (Admin)' if role == 'admin' else 'ผู้ใช้งานทั่วไป'}</div>
              <div class="mem-sidebar-user-status">สถานะ: เข้าสู่ระบบสำเร็จ</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="mem-menu-title">เมนู</div>', unsafe_allow_html=True)

        def nav_btn(label: str, page_key: str) -> None:
            active = st.session_state.get("active_page", "dashboard") == page_key
            css_class = "mem-menu-btn-active" if active else "mem-menu-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button(label, key=f"nav_{page_key}"):
                st.session_state.active_page = page_key
                st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # admin เห็นทุกเมนู
        if role == "admin":
            nav_btn("หน้าหลัก", "dashboard")
            nav_btn("รายการครุภัณฑ์", "assets")
            nav_btn("แจ้งซ่อม / บำรุงรักษา", "maintenance")
            nav_btn("แผนสอบเทียบ", "calibration")
            nav_btn("รายงานสรุป", "reports")
            nav_btn("สแกน / QR Code", "qr")
        else:
            nav_btn("รายการครุภัณฑ์", "assets")
            nav_btn("สแกน / QR Code", "qr")

        st.markdown('<div class="mem-logout-btn">', unsafe_allow_html=True)
        if st.button("Logout", key="btn_logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = {}
            st.session_state.active_page = "dashboard"
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# Page: Dashboard
# ==========================

def page_dashboard() -> None:
    df = load_equipment_data()

    st.markdown('<div class="mem-page-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mem-page-header">
          <div class="mem-page-title">ภาพรวมระบบ MEM System</div>
          <div class="mem-page-subtitle">
            สรุปสถานะครุภัณฑ์ เครื่องมือแพทย์ การแจ้งซ่อม และแผนสอบเทียบในห้องปฏิบัติการ
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_assets = len(df) if not df.empty else 0
    status_counts = (
        df[MAINT_STATUS_COL].value_counts().to_dict() if not df.empty else {}
    )
    waiting_maint = status_counts.get("แจ้งซ่อมแล้ว - กำลังดำเนินการ", 0)
    done_maint = status_counts.get("ซ่อมเสร็จแล้ว", 0)

    today = date.today()
    this_year = today.year
    this_month = today.month

    st.markdown('<div class="mem-stat-grid">', unsafe_allow_html=True)
    # การ์ด 1: จำนวนครุภัณฑ์
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="mem-stat-card">
              <div class="mem-stat-label">จำนวนครุภัณฑ์ทั้งหมด</div>
              <div class="mem-stat-value">{total_assets}</div>
              <div class="mem-stat-pill">ไฟล์: {DEFAULT_EXCEL_NAME}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="mem-stat-card">
              <div class="mem-stat-label">แจ้งซ่อมที่กำลังดำเนินการ</div>
              <div class="mem-stat-value">{waiting_maint}</div>
              <div class="mem-stat-pill">สถานะ: กำลังติดตามงานซ่อม</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="mem-stat-card">
              <div class="mem-stat-label">ซ่อมเสร็จแล้ว</div>
              <div class="mem-stat-value">{done_maint}</div>
              <div class="mem-stat-pill">บันทึกผลการซ่อมในระบบแล้ว</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="mem-stat-card">
              <div class="mem-stat-label">เดือนปัจจุบัน</div>
              <div class="mem-stat-value">{this_month:02d}/{this_year}</div>
              <div class="mem-stat-pill">อัปเดตข้อมูลล่าสุด {today.strftime("%d/%m/%Y")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # กราฟสรุปสถานะแจ้งซ่อม
    st.markdown(
        """
        <div class="mem-card">
          <div class="mem-card-title">สรุปสถานะการแจ้งซ่อม / บำรุงรักษา</div>
          <div class="mem-card-subtitle">
            แสดงจำนวนครุภัณฑ์ในแต่ละสถานะ เพื่อช่วยติดตามงานซ่อมและการบำรุงรักษา
          </div>
        """,
        unsafe_allow_html=True,
    )

    status_df = df[[MAINT_STATUS_COL]].copy()
    status_df["จำนวน"] = 1
    status_df = status_df.groupby(MAINT_STATUS_COL)["จำนวน"].sum().reset_index()

    chart = (
        alt.Chart(status_df)
        .mark_bar()
        .encode(
            x=alt.X(MAINT_STATUS_COL, title="สถานะการแจ้งซ่อม"),
            y=alt.Y("จำนวน:Q", title="จำนวนครุภัณฑ์"),
            tooltip=[MAINT_STATUS_COL, "จำนวน"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# ฟอร์มแก้ไขรายละเอียดครุภัณฑ์ (ใช้ทั้งหน้า assets และ QR)
# ==========================

def render_asset_detail_form(df: pd.DataFrame, row_idx: Any, role: str, from_qr: bool = False) -> None:
    row = df.loc[row_idx]
    code = str(row.get(ASSET_CODE_COL, "ไม่ระบุ"))
    name_col = find_name_column(df)
    name_val = str(row.get(name_col, "")) if name_col else ""

    is_admin = (role == "admin")

    st.markdown(
        f"""
        <div class="mem-card">
          <div class="mem-asset-header">{name_val or 'รายละเอียดครุภัณฑ์'}</div>
          <div class="mem-asset-sub">
            รหัสเครื่องมือ: <strong>{code or '-'}</strong>
            {" | หน้านี้เปิดจาก QR Code" if from_qr else ""}
          </div>
        """,
        unsafe_allow_html=True,
    )

    # ค่าเริ่มต้น
    maint_status = str(row.get(MAINT_STATUS_COL, MAINT_STATUS_CHOICES[0]))
    maint_request_date_raw = row.get(MAINT_REQUEST_DATE_COL, "")
    maint_due_date_raw = row.get(MAINT_DUE_DATE_COL, "")
    maint_est_days_raw = row.get(MAINT_EST_DAYS_COL, "")
    maint_result = str(row.get(MAINT_RESULT_COL, ""))
    maint_note = str(row.get(MAINT_NOTE_COL, ""))
    user_note = str(row.get(USER_NOTE_COL, ""))

    def to_date(v) -> Optional[date]:
        if isinstance(v, date):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str) and v:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(v, fmt).date()
                except Exception:
                    continue
        return None

    maint_request_date = to_date(maint_request_date_raw) or date.today()
    maint_due_date = to_date(maint_due_date_raw)
    try:
        maint_est_days = int(maint_est_days_raw)
    except Exception:
        maint_est_days = 0

    with st.form(key=f"asset_form_{row_idx}_{'qr' if from_qr else 'page'}"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("รหัสเครื่องมือ", value=code, disabled=True)
        if name_col:
            with c2:
                st.text_input("ชื่อครุภัณฑ์ / เครื่องมือ", value=name_val, disabled=True)

        st.write("---")

        # หมายเหตุจากผู้ใช้งาน (ทุกคนเขียนได้)
        user_note_new = st.text_area(
            "หมายเหตุจากผู้ใช้งาน (ใช้บันทึกการใช้งาน ปัญหาที่พบ ฯลฯ)",
            value=user_note,
            height=100,
        )

        st.write("")

        if is_admin:
            st.markdown("**ข้อมูลการแจ้งซ่อม / บำรุงรักษา (สำหรับผู้ดูแลระบบ)**")
            col_a, col_b = st.columns(2)
            with col_a:
                maint_status_new = st.selectbox(
                    "สถานะการแจ้งซ่อม",
                    MAINT_STATUS_CHOICES,
                    index=MAINT_STATUS_CHOICES.index(maint_status) if maint_status in MAINT_STATUS_CHOICES else 0,
                )
                maint_request_date_new = st.date_input(
                    "วันที่แจ้งซ่อมล่าสุด",
                    value=maint_request_date,
                )
                maint_est_days_new = st.number_input(
                    "คาดว่าซ่อมใช้เวลากี่วัน",
                    min_value=0,
                    max_value=365,
                    value=maint_est_days,
                    step=1,
                )
            with col_b:
                maint_due_date_new = st.date_input(
                    "กำหนดซ่อมเสร็จ (ถ้ามี)",
                    value=maint_due_date or date.today(),
                )
                maint_result_new = st.selectbox(
                    "ผลการซ่อม / การประเมินสภาพ",
                    MAINT_RESULT_CHOICES,
                    index=MAINT_RESULT_CHOICES.index(maint_result) if maint_result in MAINT_RESULT_CHOICES else 0,
                )
                maint_note_new = st.text_area(
                    "หมายเหตุการซ่อม / บำรุงรักษา",
                    value=maint_note,
                    height=80,
                )
        else:
            st.markdown("**แจ้งซ่อม / ปัญหาที่พบ (ผู้ใช้งานทั่วไป)**")
            report_choice = st.radio(
                "ต้องการแจ้งซ่อมอุปกรณ์นี้หรือไม่",
                ["ยังไม่แจ้งซ่อม", "แจ้งซ่อมอุปกรณ์นี้"],
                index=1 if maint_status == "แจ้งซ่อมแล้ว - กำลังดำเนินการ" else 0,
            )
            maint_note_new = st.text_area(
                "รายละเอียดปัญหาที่ต้องการแจ้งซ่อม (ถ้ามี)",
                value=maint_note if maint_note else "",
                height=80,
            )
            maint_status_new = maint_status
            maint_request_date_new = maint_request_date
            maint_est_days_new = maint_est_days
            maint_due_date_new = maint_due_date or date.today()
            maint_result_new = maint_result

            if report_choice == "แจ้งซ่อมอุปกรณ์นี้":
                maint_status_new = "แจ้งซ่อมแล้ว - กำลังดำเนินการ"
                maint_request_date_new = date.today()

        submitted = st.form_submit_button("บันทึกข้อมูล")

        if submitted:
            # update dataframe
            df.at[row_idx, USER_NOTE_COL] = user_note_new

            df.at[row_idx, MAINT_STATUS_COL] = maint_status_new
            df.at[row_idx, MAINT_REQUEST_DATE_COL] = maint_request_date_new
            df.at[row_idx, MAINT_EST_DAYS_COL] = maint_est_days_new
            df.at[row_idx, MAINT_DUE_DATE_COL] = maint_due_date_new
            df.at[row_idx, MAINT_RESULT_COL] = maint_result_new
            df.at[row_idx, MAINT_NOTE_COL] = maint_note_new

            save_equipment_data(df)
            st.success("บันทึกข้อมูลเรียบร้อยแล้ว")
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# Page: รายการครุภัณฑ์
# ==========================

def page_assets(role: str) -> None:
    df = load_equipment_data()

    st.markdown('<div class="mem-page-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mem-page-header">
          <div class="mem-page-title">รายการครุภัณฑ์ทั้งหมด</div>
          <div class="mem-page-subtitle">
            สามารถค้นหาและเลือกดูรายละเอียดครุภัณฑ์ได้ ผู้ใช้ทั่วไปสามารถกรอกหมายเหตุและแจ้งซ่อมได้
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    name_col = find_name_column(df)
    search_text = st.text_input("ค้นหาจากรหัสหรือชื่อครุภัณฑ์", "")

    filtered_df = df.copy()
    if search_text:
        search_lower = search_text.lower()
        cond = False
        if ASSET_CODE_COL in filtered_df.columns:
            cond = cond | filtered_df[ASSET_CODE_COL].astype(str).str.lower().str.contains(search_lower)
        if name_col:
            cond = cond | filtered_df[name_col].astype(str).str.lower().str.contains(search_lower)
        filtered_df = filtered_df[cond]

    if filtered_df.empty:
        st.warning("ไม่พบข้อมูลที่ตรงกับคำค้นหา")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # เลือกครุภัณฑ์จาก drop-down
    index_list: List[Any] = list(filtered_df.index)

    def format_opt(idx: Any) -> str:
        row = filtered_df.loc[idx]
        code = str(row.get(ASSET_CODE_COL, ""))
        name = str(row.get(name_col, "")) if name_col else ""
        if code and name:
            return f"{code} – {name}"
        return code or name or "(ไม่มีชื่อ)"

    selected_idx = st.selectbox(
        "เลือกครุภัณฑ์ที่ต้องการดู / แก้ไข",
        options=index_list,
        format_func=format_opt,
    )

    render_asset_detail_form(df, selected_idx, role, from_qr=False)

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# Page: แจ้งซ่อม / บำรุงรักษา (ภาพรวม)
# ==========================

def page_maintenance() -> None:
    df = load_equipment_data()

    st.markdown('<div class="mem-page-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mem-page-header">
          <div class="mem-page-title">ภาพรวมการแจ้งซ่อมและบำรุงรักษา</div>
          <div class="mem-page-subtitle">
            แสดงรายการครุภัณฑ์ที่มีการแจ้งซ่อมและสถานะต่าง ๆ เพื่อให้ผู้ดูแลระบบติดตามงานได้สะดวก
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    waiting_df = df[df[MAINT_STATUS_COL] == "แจ้งซ่อมแล้ว - กำลังดำเนินการ"]
    done_df = df[df[MAINT_STATUS_COL] == "ซ่อมเสร็จแล้ว"]

    st.markdown("#### รายการที่กำลังดำเนินการซ่อม")
    if waiting_df.empty:
        st.write("– ไม่มีรายการที่กำลังดำเนินการ –")
    else:
        cols_show = [c for c in [ASSET_CODE_COL, find_name_column(df), MAINT_REQUEST_DATE_COL, MAINT_NOTE_COL] if c]
        st.dataframe(waiting_df[cols_show], use_container_width=True, hide_index=True)

    st.markdown("#### รายการที่ซ่อมเสร็จแล้ว")
    if done_df.empty:
        st.write("– ยังไม่มีรายการที่ซ่อมเสร็จ –")
    else:
        cols_show = [c for c in [ASSET_CODE_COL, find_name_column(df), MAINT_REQUEST_DATE_COL, MAINT_RESULT_COL] if c]
        st.dataframe(done_df[cols_show], use_container_width=True, hide_index=True)

    st.info("หากต้องการแก้ไขรายละเอียดเฉพาะรายการ สามารถไปที่เมนู 'รายการครุภัณฑ์' แล้วเลือกแก้ไขทีละรายการได้")

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# Page: แผนสอบเทียบ (Calibration Plan)
# ==========================

CAL_PLAN_SIMPLE_PATH = DATA_DIR / "calibration_plan_simple.xlsx"

import calendar as _calendar


def load_calibration_plan() -> Optional[pd.DataFrame]:
    if not CAL_PLAN_SIMPLE_PATH.exists():
        return None
    try:
        df = pd.read_excel(CAL_PLAN_SIMPLE_PATH)
    except Exception:
        return None
    return df


def build_month_calendar(year: int, month: int, events_by_day: Dict[int, int]) -> str:
    # สร้าง HTML calendar เป็น grid
    cal = _calendar.Calendar(firstweekday=0)  # Monday=0
    weeks = cal.monthdayscalendar(year, month)

    thai_months = [
        "",
        "ม.ค.",
        "ก.พ.",
        "มี.ค.",
        "เม.ย.",
        "พ.ค.",
        "มิ.ย.",
        "ก.ค.",
        "ส.ค.",
        "ก.ย.",
        "ต.ค.",
        "พ.ย.",
        "ธ.ค.",
    ]

    html = [f'<div class="mem-cal-month-card"><div class="mem-cal-month-title">{thai_months[month]} {year + 543}</div>']
    html.append('<div class="mem-cal-grid">')
    day_names = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
    for d in day_names:
        html.append(f'<div class="mem-cal-day-header">{d}</div>')
    for week in weeks:
        for day in week:
            if day == 0:
                html.append('<div class="mem-cal-day"></div>')
            else:
                has = day in events_by_day and events_by_day[day] > 0
                cls = "mem-cal-day has-event" if has else "mem-cal-day"
                html.append(f'<div class="{cls}">{day}</div>')
    html.append("</div></div>")
    return "".join(html)


def page_calibration() -> None:
    df_cal = load_calibration_plan()

    st.markdown('<div class="mem-page-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mem-page-header">
          <div class="mem-page-title">แผนการสอบเทียบเครื่องมือ (Calibration Plan)</div>
          <div class="mem-page-subtitle">
            ใช้สำหรับวางแผนสอบเทียบรายเดือน และดูรายการเครื่องมือที่ต้องสอบเทียบในแต่ละเดือนจากไฟล์ calibration_plan_simple.xlsx
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_cal is None or df_cal.empty:
        st.info("ยังไม่พบไฟล์ calibration_plan_simple.xlsx หรือไม่มีข้อมูล กรุณาเตรียมไฟล์นี้ในโฟลเดอร์ data")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # คาดว่าไฟล์มีคอลัมน์: 'ชื่อเครื่องมือ', 'ID', 'S/N', 'เดือนสอบเทียบ', 'หมายเหตุ'
    month_col_candidates = [c for c in df_cal.columns if "เดือน" in str(c)]
    if month_col_candidates:
        month_col = month_col_candidates[0]
    else:
        month_col = None

    name_col = None
    for c in df_cal.columns:
        if "ชื่อ" in str(c) and ("เครื่อง" in str(c) or "ครุภัณฑ์" in str(c) or "อุปกรณ์" in str(c)):
            name_col = c
            break

    # ตัวเลือกเดือน
    thai_month_labels = [
        "ม.ค.",
        "ก.พ.",
        "มี.ค.",
        "เม.ย.",
        "พ.ค.",
        "มิ.ย.",
        "ก.ค.",
        "ส.ค.",
        "ก.ย.",
        "ต.ค.",
        "พ.ย.",
        "ธ.ค.",
    ]
    month_numbers = list(range(1, 13))

    today = date.today()
    default_month = today.month

    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        st.markdown(
            """
            <div class="mem-cal-header">ตารางแผนสอบเทียบรายเดือน</div>
            <div class="mem-cal-sub">
              เลือกเดือนที่ต้องการดูรายการสอบเทียบ ระบบจะแสดงปฏิทินและรายการเครื่องมือที่เกี่ยวข้อง
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_sel2:
        month_idx = st.selectbox(
            "เลือกเดือนสำหรับแสดงรายการ",
            options=month_numbers,
            index=default_month - 1,
            format_func=lambda m: thai_month_labels[m - 1],
        )
    selected_month = month_idx
    selected_year = today.year

    # เตรียมข้อมูล events ให้ปฏิทิน: ใช้วันที 1 เป็นตัวแทน หรือหากมีคอลัมน์วันที่ก็ใช้จริง
    events_by_day_current = {1: len(df_cal)}
    events_by_day_next = {1: len(df_cal)}

    st.markdown('<div class="mem-cal-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="mem-cal-months">', unsafe_allow_html=True)

    # เดือนที่เลือก
    html_current = build_month_calendar(selected_year, selected_month, events_by_day_current)
    st.markdown(html_current, unsafe_allow_html=True)

    # เดือนถัดไป
    next_month = selected_month + 1
    next_year = selected_year
    if next_month == 13:
        next_month = 1
        next_year += 1
    html_next = build_month_calendar(next_year, next_month, events_by_day_next)
    st.markdown(html_next, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close mem-cal-months
    st.markdown("</div>", unsafe_allow_html=True)  # close mem-cal-wrapper

    # รายการเครื่องมือในเดือนที่เลือก
    if month_col:
        month_filtered = df_cal[df_cal[month_col] == selected_month]
    else:
        month_filtered = df_cal.copy()

    st.markdown(
        """
        <div class="mem-card">
          <div class="mem-card-title">รายการเครื่องมือในแผนสอบเทียบของเดือนที่เลือก</div>
          <div class="mem-card-subtitle">
            แสดงเฉพาะเครื่องมือที่กำหนดเดือนสอบเทียบตรงกับเดือนที่เลือก หากไม่ระบุเดือนในไฟล์ จะถูกแสดงทุกเดือน
          </div>
        """,
        unsafe_allow_html=True,
    )

    if month_filtered.empty:
        st.write("– ยังไม่มีรายการเครื่องมือสำหรับเดือนนี้ –")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    html_cards = ['<div class="cal-equip-list">']
    for _, r in month_filtered.iterrows():
        title = str(r.get(name_col, r.get("ชื่อเครื่องมือ", "ไม่ระบุชื่อเครื่องมือ")))
        equip_id = str(r.get("ID", r.get("รหัส", "nan")))
        sn = str(r.get("S/N", r.get("Serial", "nan")))
        note = str(r.get("หมายเหตุ", "ไม่ระบุ"))
        html_cards.append(
            f"""
            <div class="cal-equip-card">
              <div class="cal-equip-title">{title}</div>
              <div class="cal-equip-meta"><span>ID: {equip_id}</span> | <span>S/N: {sn}</span></div>
              <div class="cal-equip-note">หมายเหตุ: {note}</div>
            </div>
            """
        )
    html_cards.append("</div>")  # close cal-equip-list
    st.markdown("".join(html_cards), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # close mem-card
    st.markdown("</div>", unsafe_allow_html=True)  # close mem-page-container


# ==========================
# Page: รายงานสรุป
# ==========================

def page_reports() -> None:
    df = load_equipment_data()

    st.markdown('<div class="mem-page-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mem-page-header">
          <div class="mem-page-title">รายงานสรุปการใช้งานระบบ</div>
          <div class="mem-page-subtitle">
            กราฟสรุปข้อมูลครุภัณฑ์ การแจ้งซ่อม และการบันทึกหมายเหตุจากผู้ใช้งาน
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # รายการที่มีหมายเหตุจากผู้ใช้
    note_df = df[df[USER_NOTE_COL].astype(str).str.strip() != ""]
    st.markdown("#### รายการที่มีหมายเหตุจากผู้ใช้งาน")
    if note_df.empty:
        st.write("– ยังไม่มีการบันทึกหมายเหตุจากผู้ใช้งาน –")
    else:
        cols_show = [c for c in [ASSET_CODE_COL, find_name_column(df), USER_NOTE_COL, MAINT_STATUS_COL] if c]
        st.dataframe(note_df[cols_show], hide_index=True, use_container_width=True)

    st.write("---")

    # กราฟแจ้งซ่อมตามเดือน (จากวันที่แจ้งซ่อมล่าสุด)
    maint_df = df[df[MAINT_REQUEST_DATE_COL].notna() & (df[MAINT_REQUEST_DATE_COL] != "")]
    if not maint_df.empty:
        def to_month(d) -> str:
            if isinstance(d, datetime):
                dt = d
            elif isinstance(d, date):
                dt = datetime(d.year, d.month, d.day)
            elif isinstance(d, str) and d:
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        dt = datetime.strptime(d, fmt)
                        break
                    except Exception:
                        continue
                else:
                    return ""
            else:
                return ""
            return dt.strftime("%Y-%m")

        maint_df = maint_df.copy()
        maint_df["month"] = maint_df[MAINT_REQUEST_DATE_COL].apply(to_month)
        maint_df = maint_df[maint_df["month"] != ""]
        if not maint_df.empty:
            month_count = maint_df.groupby("month")[ASSET_CODE_COL].count().reset_index()
            month_count.rename(columns={ASSET_CODE_COL: "จำนวนที่แจ้งซ่อม"}, inplace=True)

            st.markdown("#### กราฟจำนวนการแจ้งซ่อม แยกตามเดือน")
            chart = (
                alt.Chart(month_count)
                .mark_bar()
                .encode(
                    x=alt.X("month:O", title="เดือนที่แจ้งซ่อม"),
                    y=alt.Y("จำนวนที่แจ้งซ่อม:Q", title="จำนวนรายการ"),
                    tooltip=["month", "จำนวนที่แจ้งซ่อม"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# Page: QR / Scan
# ==========================

def page_qr(role: str) -> None:
    df = load_equipment_data()
    st.markdown('<div class="mem-page-container">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mem-page-header">
          <div class="mem-page-title">สแกน / QR Code – แก้ไขข้อมูลแบบรวดเร็ว</div>
          <div class="mem-page-subtitle">
            ใช้ลิงก์ QR Code ที่ผูกกับรหัสเครื่องมือ เพื่อเปิดมาหน้านี้แล้วแก้ไขข้อมูลแจ้งซ่อมและหมายเหตุได้ทันทีแบบเรียลไทม์
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    qr_code_param = get_query_param("code", "") or get_query_param("asset", "")

    code_input = st.text_input(
        "รหัสเครื่องมือห้องปฏิบัติการ (จะถูกกรอกให้อัตโนมัติเมื่อเปิดจากลิงก์ QR)",
        value=str(qr_code_param or ""),
        key="qr_code_input",
    )

    if not code_input:
        st.info("กรุณากรอกรหัสเครื่องมือ หรือทดลองสแกน QR ที่ชี้มาที่ URL ของหน้านี้พร้อม parameter ?code=รหัส")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if ASSET_CODE_COL not in df.columns:
        st.error(f"ไม่พบคอลัมน์ '{ASSET_CODE_COL}' ในไฟล์ Excel")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    mask = df[ASSET_CODE_COL].astype(str) == str(code_input)
    if not mask.any():
        st.warning("ไม่พบครุภัณฑ์ที่มีรหัสนี้ในไฟล์ กรุณาตรวจสอบรหัสอีกครั้ง")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    row_idx = df.index[mask][0]
    render_asset_detail_form(df, row_idx, role, from_qr=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# MAIN
# ==========================

def main() -> None:
    # เตรียม session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = {}
    if "active_page" not in st.session_state:
        st.session_state.active_page = "dashboard"

    if not st.session_state.logged_in:
        render_auth_page()
        return

    # หลังล็อกอิน
    set_main_style()
    user = st.session_state.get("current_user", {}) or {}
    role = user.get("role", "user")

    sidebar_nav()

    active_page = st.session_state.get("active_page", "dashboard")

    if role != "admin" and active_page not in ("assets", "qr"):
        active_page = "assets"
        st.session_state.active_page = active_page

    if active_page == "dashboard":
        page_dashboard()
    elif active_page == "assets":
        page_assets(role)
    elif active_page == "maintenance":
        page_maintenance()
    elif active_page == "calibration":
        page_calibration()
    elif active_page == "reports":
        page_reports()
    elif active_page == "qr":
        page_qr(role)
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
