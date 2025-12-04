# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH, get_excel_path
from auth import authenticate_user, is_authed, logout

# =========================
# CONFIG / CONSTANTS
# =========================
ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"
IMAGE_DIR = Path("asset_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

MAINT_STATUS_CHOICES = [
    "ยังไม่เคยแจ้งซ่อม",
    "แจ้งซ่อมแล้ว - กำลังดำเนินการ",
    "ซ่อมเสร็จแล้ว",
    "ปลดระวาง / รอจำหน่าย",
]

st.set_page_config(
    page_title="MEM System – Medical Equipment Management",
    page_icon="🩺",
    layout="wide",
)


# =========================
# Excel Helpers (ใช้ไฟล์เดียวกับหน้า QR)
# =========================
def get_available_excel_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([p.name for p in DATA_DIR.glob("*.xls*")])


def init_excel_file_name():
    """เตรียมชื่อไฟล์ Excel ใน session_state
    - ถ้ามีไฟล์ในโฟลเดอร์ data → เลือกจากนั้น
    - ถ้าไม่มี → ใช้ DEFAULT_EXCEL_PATH จาก config
    """
    if "excel_file_name" in st.session_state:
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = get_available_excel_files()

    # ถ้า config มีไฟล์ default ให้ใช้ตัวนั้นก่อน
    if DEFAULT_EXCEL_PATH.exists():
        st.session_state["excel_file_name"] = DEFAULT_EXCEL_PATH.name
        return

    if files:
        st.session_state["excel_file_name"] = files[0]
    else:
        # กรณียังไม่มีไฟล์เลย
        st.session_state["excel_file_name"] = None


def get_current_excel_path() -> Path | None:
    init_excel_file_name()
    name = st.session_state.get("excel_file_name")
    if not name:
        return None
    return DATA_DIR / name


def load_equipment_data() -> pd.DataFrame:
    path = get_current_excel_path()
    if path is None or not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)

        if "สถานะแจ้งซ่อม" not in df.columns:
            df["สถานะแจ้งซ่อม"] = MAINT_STATUS_CHOICES[0]
        if "รูปภาพครุภัณฑ์" not in df.columns:
            df["รูปภาพครุภัณฑ์"] = ""

        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def save_equipment_data(df: pd.DataFrame):
    path = get_current_excel_path()
    if path is None:
        st.error("ยังไม่ได้เลือกไฟล์ Excel ที่จะบันทึก")
        return

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_excel(path, index=False)
        st.success(f"บันทึกการแก้ไขลงไฟล์: {path.name} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")


# =========================
# Helper: รูป / QR
# =========================
def get_image_path_from_row(row: pd.Series) -> Path | None:
    val = str(row.get("รูปภาพครุภัณฑ์", "") or "").strip()
    if not val:
        return None

    p = Path(val)
    if not p.is_absolute():
        p = IMAGE_DIR / p.name
    return p


def save_uploaded_image(uploaded, asset_code: str) -> str:
    suffix = Path(uploaded.name).suffix or ".png"
    safe_code = asset_code.replace("/", "_").replace("\\", "_").replace(" ", "_")
    filename = f"{safe_code}{suffix}"
    target_path = IMAGE_DIR / filename
    with open(target_path, "wb") as f:
        f.write(uploaded.getbuffer())
    return filename


def generate_qr_bytes_for_url(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# =========================
# STYLE: Landing / Login / Main
# =========================
def set_landing_style():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background: radial-gradient(circle at top,#e0f2fe 0,#f9fafb 55%,#eef2ff 100%);
        }
        [data-testid="stHeader"]{
            background: transparent;
        }
        .landing-container{
            max-width: 900px;
            margin: 3.5rem auto 3rem auto;
            text-align: center;
        }
        .landing-badge{
            display:inline-block;
            padding:4px 14px;
            border-radius:999px;
            background:rgba(15,23,42,0.06);
            font-size:12px;
            color:#4b5563;
            margin-bottom:0.75rem;
        }
        .landing-title{
            font-size:38px;
            font-weight:800;
            line-height:1.25;
            color:#020617;
            margin-bottom:0.75rem;
        }
        .landing-highlight{
            color:#2563eb;
        }
        .landing-sub{
            font-size:13px;
            color:#6b7280;
            max-width:650px;
            margin:0 auto 1.7rem auto;
        }
        .landing-btn-row{
            display:flex;
            justify-content:center;
            gap:12px;
            margin-bottom:0.75rem;
        }
        .landing-btn-primary button{
            background:#2563eb;
            color:#ffffff;
            border-radius:999px;
            height:2.8rem;
            padding:0 2.5rem;
            font-weight:600;
            border:none;
            box-shadow:0 18px 35px rgba(37,99,235,0.25);
        }
        .landing-btn-outline button{
            border-radius:999px;
            height:2.8rem;
            padding:0 2.5rem;
            font-weight:500;
            border:1px solid #cbd5f5;
            background:rgba(255,255,255,0.9);
            color:#1f2933;
        }
        .landing-feature-wrapper{
            max-width:1050px;
            margin:1.5rem auto 2.5rem auto;
        }
        .landing-feature-grid{
            display:grid;
            grid-template-columns:repeat(3,minmax(0,1fr));
            gap:16px;
        }
        .landing-feature-card{
            background:#ffffff;
            border-radius:26px;
            padding:20px 22px;
            box-shadow:0 18px 40px rgba(15,23,42,0.12);
            border:1px solid rgba(209,213,219,0.7);
            text-align:left;
        }
        .landing-feature-icon-wrapper{
            width:40px;
            height:40px;
            border-radius:999px;
            display:flex;
            align-items:center;
            justify-content:center;
            margin-bottom:10px;
            background:#fef3c7;
        }
        .card-icon-2{ background:#fee2e2; }
        .card-icon-3{ background:#dbeafe; }

        .landing-feature-icon{
            font-size:22px;
        }
        .landing-feature-title{
            font-size:15px;
            font-weight:700;
            margin-bottom:4px;
            color:#111827;
        }
        .landing-feature-text{
            font-size:12px;
            color:#6b7280;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_login_style():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background: #3B4251;
        }
        [data-testid="stHeader"]{
            background: transparent;
        }
        .block-container{
            max-width: 460px !important;
            padding-top: 3rem !important;
            padding-bottom: 3rem !important;
            margin: 4rem auto 3rem auto;
            background: #FFFFFF;
            border-radius: 28px;
            box-shadow: 0 28px 60px rgba(0,0,0,0.55);
        }
        .mem-login-title{
            text-align: center;
            font-size: 26px;
            font-weight: 600;
            margin-bottom: 0.4rem;
            color: #111827;
        }
        .mem-login-sub{
            text-align: center;
            font-size: 12px;
            color: #6B7280;
            margin-bottom: 1.6rem;
        }
        .mem-login-footer{
            text-align:center;
            font-size: 12px;
            color: #9CA3AF;
            margin-top: 1rem;
        }
        .stTextInput > label{
            font-size: 13px;
            color: #4B5563;
        }
        .stTextInput > div > div{
            border-radius: 999px;
            border: 1px solid #E5E7EB;
            background: #F9FAFB;
            padding: 0 0.75rem;
            box-shadow: inset 0 1px 2px rgba(15,23,42,0.06);
        }
        .mem-login-btn button{
            background: #020617;
            color: #FFFFFF;
            border-radius: 999px;
            height: 2.7rem;
            border: none;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_main_style():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background: #F3F4F6;
        }
        [data-testid="stHeader"]{
            background: #FFFFFF;
        }
        .block-container{
            max-width: 1200px !important;
            padding-top: 2.0rem !important;
            padding-bottom: 1.5rem !important;
            margin: 0 auto;
            background: transparent;
            box-shadow: none;
        }
        [data-testid="stSidebar"]{
            background: #1F2430;
        }
        [data-testid="stSidebar"] > div{
            padding-top: 1.1rem;
            padding-bottom: 1.1rem;
        }
        .mem-sidebar-user{
            background: #0F172A;
            border-radius: 20px;
            padding: 14px 16px;
            color: #E5E7EB;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            margin-bottom: 12px;
        }
        .mem-sidebar-user-name{
            font-weight: 700;
            font-size: 16px;
            color: #F9FAFB;
        }
        .mem-sidebar-user-sub{
            font-size: 12px;
            color: #9CA3AF;
        }
        .mem-menu-title{
            font-size: 13px;
            font-weight: 600;
            color: #F9FAFB;
            margin-bottom: 6px;
        }
        .mem-menu-btn,
        .mem-menu-btn-active{
            width: 100%;
            margin-bottom: 2px;
        }
        .mem-menu-btn button,
        .mem-menu-btn-active button{
            width: 100%;
            text-align: left;
            border-radius: 999px;
            min-height: 2.0rem;
            font-size: 13px;
            padding-top: 0.15rem;
            padding-bottom: 0.15rem;
        }
        .mem-menu-btn-active button{
            background: #F97316 !important;
            color: #111827 !important;
            font-weight: 700;
        }
        .mem-page-title{
            font-size: 30px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.5rem;
        }
        .mem-page-subtitle{
            font-size: 13px;
            color: #6B7280;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# หน้า Landing
# =========================
def landing_page():
    set_landing_style()

    st.markdown('<div class="landing-container">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="landing-badge">
            ระบบบริหารจัดการครุภัณฑ์เครื่องมือแพทย์ & ห้องปฏิบัติการ
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="landing-title">
            บริหารเครื่องมือแพทย์อย่างมืออาชีพ เพื่อผลการตรวจที่แม่นยำและ<br>
            ปลอดภัย แบบ <span class="landing-highlight">Real-time</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="landing-sub">
            จัดการครุภัณฑ์เครื่องมือแพทย์ ตั้งแต่ทะเบียน ประวัติการใช้งาน การแจ้งซ่อม 
            และข้อมูลห้องปฏิบัติการ ให้ทุกคนในทีมใช้ข้อมูลชุดเดียวกัน รองรับการตรวจประเมินคุณภาพ
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-btn-row">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="landing-btn-outline">', unsafe_allow_html=True)
        btn_start = st.button("เริ่มใช้งานระบบ", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="landing-btn-primary">', unsafe_allow_html=True)
        btn_login = st.button("เข้าสู่ระบบ", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # การ์ด 3 ใบด้านล่าง
    st.markdown('<div class="landing-feature-wrapper">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="landing-feature-grid">

          <div class="landing-feature-card">
            <div class="landing-feature-icon-wrapper">
              <span class="landing-feature-icon">✅</span>
            </div>
            <div class="landing-feature-title">ทะเบียนครุภัณฑ์ละเอียดครบถ้วน</div>
            <div class="landing-feature-text">
              จัดเก็บข้อมูลครุภัณฑ์แต่ละรายการ เช่น รุ่น หมายเลขเครื่อง Serial Number มูลค่า 
              และสถานะการใช้งานปัจจุบัน
            </div>
          </div>

          <div class="landing-feature-card">
            <div class="landing-feature-icon-wrapper card-icon-2">
              <span class="landing-feature-icon">📲</span>
            </div>
            <div class="landing-feature-title">ตรวจเช็คครุภัณฑ์หน้างานด้วยสแกน QR Code</div>
            <div class="landing-feature-text">
              ติด QR ที่อุปกรณ์และสแกนเพื่อเปิดหน้าข้อมูลครุภัณฑ์ แสดงรูป ประวัติ 
              และสถานะการแจ้งซ่อมได้ทันที
            </div>
          </div>

          <div class="landing-feature-card">
            <div class="landing-feature-icon-wrapper card-icon-3">
              <span class="landing-feature-icon">📊</span>
            </div>
            <div class="landing-feature-title">Dashboard สรุปภาพรวมแบบ Real-time</div>
            <div class="landing-feature-text">
              แสดงจำนวนครุภัณฑ์ตามสถานะ ห้องที่มีครุภัณฑ์มากที่สุด 
              และข้อมูลที่ใช้จัดเตรียมเอกสารตรวจประเมินมาตรฐานต่าง ๆ
            </div>
          </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ถ้ากดปุ่ม → ไปหน้า login
    if btn_start or btn_login:
        st.session_state.view = "login"
        st.experimental_rerun() if False else st.rerun()


# =========================
# หน้า Login
# =========================
def login_page():
    set_login_style()

    st.markdown('<div class="mem-login-title">เข้าสู่ระบบ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mem-login-sub">Medical Equipment Management System</div>',
        unsafe_allow_html=True,
    )

    username = st.text_input("👤 ชื่อผู้ใช้", key="login_username")
    password = st.text_input("🔐 รหัสผ่าน", type="password", key="login_password")

    st.markdown('<div class="mem-login-btn">', unsafe_allow_html=True)
    login_clicked = st.button("เข้าสู่ระบบ", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    back_clicked = st.button("⬅️ กลับไปหน้าแรก", use_container_width=True)

    st.markdown(
        '<div class="mem-login-footer">หากลืมรหัสผ่าน กรุณาติดต่อผู้ดูแลระบบ</div>',
        unsafe_allow_html=True,
    )

    if back_clicked:
        st.session_state.view = "landing"
        st.session_state.logged_in = False
        st.rerun()

    if login_clicked:
        ok, display_name = authenticate_user(username, password)
        if ok:
            st.session_state.view = "app"
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")


# =========================
# (ตัดมาส่วน Main App เดิมของคุณ: Dashboard, รายการครุภัณฑ์, แจ้งซ่อม ฯลฯ)
# เพื่อไม่ให้ยาวเกินไป ผมใช้โครงเดียวกับที่คุณส่งมาแล้ว
# แก้เฉพาะเรื่องอ่าน/บันทึก Excel ให้ใช้ฟังก์ชันด้านบน
# =========================

def page_home():
    set_main_style()
    st.markdown(
        """
        <div class="mem-page-title">หน้าหลัก</div>
        <div class="mem-page-subtitle">
            ภาพรวมการจัดการครุภัณฑ์ และเครื่องมือห้องปฏิบัติการ
        </div>
        """,
        unsafe_allow_html=True,
    )
    # ตรงนี้ใช้ load_equipment_data() ตามที่แก้ด้านบน
    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลในไฟล์ Excel")
        return

    # ... (ส่วนสรุปสถานะ / chart / ตาราง เหมือนโค้ดเดิมของคุณ)


def main_app():
    set_main_style()

    with st.sidebar:
        st.markdown(
            f"""
            <div class="mem-sidebar-user">
              <div style="font-size:28px; font-weight:700; margin-bottom:4px;">AD</div>
              <div class="mem-sidebar-user-name">
                {st.session_state.get('display_name', 'Admin')}
              </div>
              <div class="mem-sidebar-user-sub">เข้าสู่ระบบสำเร็จ</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="mem-menu-title">เมนู</div>', unsafe_allow_html=True)

        current_menu = st.session_state.get("current_menu", "หน้าหลัก")

        def menu_button(label: str):
            is_active = current_menu == label
            css_class = "mem-menu-btn-active" if is_active else "mem-menu-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            clicked = st.button(label, use_container_width=True, key=f"menu_{label}")
            st.markdown("</div>", unsafe_allow_html=True)
            return clicked

        if menu_button("หน้าหลัก"):
            st.session_state.current_menu = "หน้าหลัก"
            st.rerun()
        if menu_button("รายการครุภัณฑ์"):
            st.session_state.current_menu = "รายการครุภัณฑ์"
            st.rerun()
        if menu_button("แจ้งซ่อม / บำรุงรักษา"):
            st.session_state.current_menu = "แจ้งซ่อม / บำรุงรักษา"
            st.rerun()
        if menu_button("รายงานสรุป"):
            st.session_state.current_menu = "รายงานสรุป"
            st.rerun()

        st.write("")
        if st.button("Logout", type="primary", use_container_width=True):
            logout()
            st.session_state.view = "landing"
            st.rerun()

    menu = st.session_state.get("current_menu", "หน้าหลัก")

    if menu == "หน้าหลัก":
        page_home()
    # elif menu == "รายการครุภัณฑ์":
    #   เรียกฟังก์ชันเดิมของคุณที่ใช้ load_equipment_data / save_equipment_data
    # ...


# =========================
# ENTRY POINT
# =========================
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "หน้าหลัก"

# ถ้าล็อกอินแล้ว ให้เข้า main_app ทันที (แม้ refresh หน้า)
if is_authed():
    main_app()
else:
    if st.session_state.view == "login":
        login_page()
    else:
        landing_page()
