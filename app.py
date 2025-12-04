import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from io import BytesIO
import qrcode
from typing import Optional

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH
from auth import authenticate_user

# =========================
# CONFIG / CONSTANTS
# =========================
st.set_page_config(
    page_title="MEM System – Medical Equipment Management",
    page_icon="🩺",
    layout="wide",
)

ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"

IMAGE_DIR = Path("asset_images")
QR_IMAGES_DIR = Path("qr_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
QR_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

MAINT_STATUS_CHOICES = [
    "ยังไม่เคยแจ้งซ่อม",
    "แจ้งซ่อมแล้ว - กำลังดำเนินการ",
    "ซ่อมเสร็จแล้ว",
    "ปลดระวาง / รอจำหน่าย",
]

# =========================
# STYLE: Landing / Login / Main
# =========================
def set_landing_style():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background: radial-gradient(circle at top,#e0f2fe 0,#f9fafb 50%,#eef2ff 100%);
        }
        [data-testid="stHeader"]{
            background: transparent;
        }
        .landing-root{
            max-width: 960px;
            margin: 2.5rem auto 3rem auto;
            text-align: center;
        }
        .landing-icon-wrapper{
            width: 70px;
            height: 70px;
            border-radius: 24px;
            background: linear-gradient(145deg,#f97316,#fb923c);
            display:flex;
            align-items:center;
            justify-content:center;
            margin: 0 auto 1rem auto;
            box-shadow:0 22px 40px rgba(251,146,60,0.45);
        }
        .landing-icon{
            font-size: 34px;
        }
        .landing-title{
            font-size: 32px;
            font-weight: 800;
            color:#020617;
            line-height:1.25;
            margin-bottom:0.75rem;
        }
        .landing-highlight{
            color:#2563eb;
        }
        .landing-sub{
            font-size: 13px;
            color:#6b7280;
            max-width: 640px;
            margin:0 auto 2.0rem auto;
        }
        .landing-buttons-row{
            display:flex;
            justify-content:center;
            gap:0.75rem;
            margin-bottom:1.25rem;
        }
        .landing-note{
            font-size:11px;
            color:#9ca3af;
        }
        .landing-feature-wrapper{
            max-width: 980px;
            margin: 2.0rem auto 0 auto;
        }
        .landing-feature-row{
            display:flex;
            flex-wrap:wrap;
            gap:18px;
            justify-content:center;
        }
        .landing-feature-card{
            flex:1 1 0;
            min-width:220px;
            max-width:280px;
            background:#ffffff;
            border-radius:24px;
            padding:18px 18px 18px 18px;
            box-shadow:0 20px 45px rgba(15,23,42,0.12);
            border:1px solid rgba(209,213,219,0.9);
            text-align:left;
        }
        .landing-feature-icon-wrapper{
            width:36px;
            height:36px;
            border-radius:14px;
            background:#fee2e2;
            display:flex;
            align-items:center;
            justify-content:center;
            margin-bottom:10px;
        }
        .card-icon-1{ background:#fef3c7; }
        .card-icon-2{ background:#e0f2fe; }
        .card-icon-3{ background:#ede9fe; }
        .landing-feature-icon{
            font-size:20px;
        }
        .landing-feature-title{
            font-size:14px;
            font-weight:700;
            color:#111827;
            margin-bottom:4px;
        }
        .landing-feature-text{
            font-size:11px;
            color:#6b7280;
        }

        /* ปุ่มบน Landing */
        .landing-btn-primary button{
            background:#2563eb;
            color:#ffffff;
            border-radius:999px;
            border:none;
            font-weight:600;
            height:2.7rem;
            padding:0 2.6rem;
            box-shadow:0 18px 35px rgba(37,99,235,0.4);
        }
        .landing-btn-primary button:hover{
            background:#1d4ed8;
        }
        .landing-btn-outline button{
            border-radius:999px;
            border:1px solid #d1d5db;
            background:#ffffff;
            color:#111827;
            font-weight:500;
            height:2.7rem;
            padding:0 2.6rem;
        }

        /* LOGIN PAGE */
        .block-container.login-container{
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
        .mem-login-btn button{
            background: #020617;
            color: #FFFFFF;
            border-radius: 999px;
            height: 2.7rem;
            border: none;
            font-weight: 500;
        }
        .mem-login-btn button:hover{
            background: #000000;
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

        /* MAIN APP */
        [data-testid="stSidebar"]{
            background:#1F2430;
        }
        [data-testid="stSidebar"] > div{
            padding-top:1.1rem;
            padding-bottom:1.1rem;
        }
        .mem-sidebar-user{
            background:#0F172A;
            border-radius:20px;
            padding:14px 16px;
            color:#E5E7EB;
            box-shadow:0 20px 40px rgba(0,0,0,0.6);
            margin-bottom:12px;
        }
        .mem-sidebar-user-name{
            font-weight:700;
            font-size:16px;
            color:#F9FAFB;
        }
        .mem-sidebar-user-sub{
            font-size:12px;
            color:#9CA3AF;
        }
        .mem-menu-title{
            font-size:13px;
            font-weight:600;
            color:#F9FAFB;
            margin-bottom:6px;
        }
        .mem-menu-btn,
        .mem-menu-btn-active{
            width:100%;
            margin-bottom:2px;
        }
        .mem-menu-btn button,
        .mem-menu-btn-active button{
            width:100%;
            text-align:left;
            border-radius:999px;
            min-height:2.0rem;
            font-size:13px;
            padding-top:0.15rem;
            padding-bottom:0.15rem;
        }
        .mem-menu-btn-active button{
            background:#F97316 !important;
            color:#111827 !important;
            font-weight:700;
        }

        .mem-page-title{
            font-size:30px;
            font-weight:800;
            color:#111827;
            margin-bottom:0.5rem;
        }
        .mem-page-subtitle{
            font-size:13px;
            color:#6B7280;
            margin-bottom:1.5rem;
        }

        .mem-hero{
            background: linear-gradient(135deg,#eef2ff,#e0f2fe);
            border-radius:26px;
            padding:18px 26px 16px 26px;
            color:#0f172a;
            box-shadow:0 18px 40px rgba(15,23,42,0.18);
            margin-bottom:22px;
            border:1px solid #dbeafe;
        }
        .mem-hero-title{
            font-size:20px;
            font-weight:700;
            margin-bottom:4px;
        }
        .mem-hero-sub{
            font-size:13px;
            opacity:0.92;
            margin-bottom:14px;
        }
        .mem-hero-metrics{
            display:flex;
            gap:10px;
            flex-wrap:wrap;
        }
        .mem-hero-metric{
            background:#ffffff;
            border-radius:18px;
            padding:8px 12px;
            min-width:165px;
            display:flex;
            flex-direction:column;
            justify-content:center;
            box-shadow:0 4px 10px rgba(15,23,42,0.05);
            border:1px solid #e5e7eb;
        }
        .mem-hero-metric-label{
            font-size:11px;
            color:#6b7280;
        }
        .mem-hero-metric-value{
            font-size:18px;
            font-weight:700;
            line-height:1.1;
            color:#111827;
        }
        .mem-hero-metric-pill{
            margin-top:4px;
            display:inline-block;
            padding:2px 8px;
            border-radius:999px;
            font-size:10px;
            background:#eff6ff;
            color:#1d4ed8;
        }
        .mem-status-legend-wrapper{
            margin-top:10px;
            overflow-x:auto;
            padding-bottom:4px;
        }
        .mem-status-legend{
            display:inline-flex;
            flex-wrap:nowrap;
            gap:8px;
            font-size:11px;
            white-space:nowrap;
        }
        .mem-status-legend-item{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:4px 10px;
            border-radius:999px;
            background:#ffffff;
            border:1px solid #e5e7eb;
            box-shadow:0 2px 6px rgba(15,23,42,0.04);
        }
        .mem-status-dot{
            width:10px;
            height:10px;
            border-radius:999px;
        }
        .mem-card{
            background:#FFFFFF;
            border-radius:32px;
            padding:20px 24px 24px 24px;
            margin-bottom:26px;
            box-shadow:0 22px 52px rgba(15,23,42,0.08);
            border:2px solid rgba(148,163,184,0.45);
            position:relative;
            overflow:hidden;
        }
        .mem-card::before{
            content:"";
            position:absolute;
            left:0; right:0; top:0;
            height:5px;
            border-radius:30px 30px 0 0;
            background:linear-gradient(90deg,#22c55e,#0ea5e9,#6366f1);
        }
        .mem-card-title{
            font-size:18px;
            font-weight:700;
            color:#111827;
            margin-bottom:0.6rem;
        }
        .mem-card-subtitle{
            font-size:12px;
            color:#9CA3AF;
            margin-bottom:0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_login_background():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background:#3B4251;
        }
        [data-testid="stHeader"]{
            background:transparent;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def set_main_background():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background:#F3F4F6;
        }
        [data-testid="stHeader"]{
            background:#FFFFFF;
        }
        .block-container{
            max-width: 1200px !important;
            padding-top: 2.0rem !important;
            padding-bottom: 1.5rem !important;
            margin: 0 auto;
            background: transparent;
            box-shadow: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Excel helpers (ใช้ร่วมกับหน้า QR)
# =========================
def get_available_excel_files() -> list[str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([p.name for p in DATA_DIR.glob("*.xls*")])


def init_excel_file_name():
    """ตั้งค่า st.session_state['excel_file_name'] ครั้งแรกเท่านั้น"""
    if "excel_file_name" in st.session_state:
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = get_available_excel_files()

    if files:
        if DEFAULT_EXCEL_NAME in files:
            st.session_state["excel_file_name"] = DEFAULT_EXCEL_NAME
        else:
            st.session_state["excel_file_name"] = files[0]
    elif DEFAULT_EXCEL_PATH.exists():
        st.session_state["excel_file_name"] = DEFAULT_EXCEL_NAME
    else:
        st.session_state["excel_file_name"] = None


def get_current_excel_path() -> Optional[Path]:
    """คืน Path ของไฟล์ Excel ที่ใช้งานอยู่"""
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
        if "บันทึกจากหน้างานล่าสุด" not in df.columns:
            df["บันทึกจากหน้างานล่าสุด"] = ""

        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def save_equipment_data(df: pd.DataFrame):
    path = get_current_excel_path()
    if path is None:
        # ถ้ายังไม่มีชื่อไฟล์ ให้ใช้ DEFAULT_EXCEL_NAME
        st.session_state["excel_file_name"] = DEFAULT_EXCEL_NAME
        path = DEFAULT_EXCEL_PATH

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_excel(path, index=False)
        st.success(f"บันทึกการแก้ไขลงไฟล์: {path.name} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")


# =========================
# รูปภาพ / QR helpers
# =========================
def get_image_path_from_row(row: pd.Series) -> Optional[Path]:
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


def get_qr_image_path_from_row(row: pd.Series) -> Optional[Path]:
    for col in ["_qr_image_path", "QR Code"]:
        if col in row.index:
            val = str(row.get(col, "") or "").strip()
            if not val:
                continue
            p = Path(val)
            if not p.is_absolute():
                p2 = QR_IMAGES_DIR / p.name
                if p2.exists():
                    return p2
            if p.exists():
                return p
    return None


def generate_qr_bytes_for_url(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# =========================
# Altair style helper
# =========================
def styled_chart(chart: alt.Chart, width: int, height: int) -> alt.Chart:
    return chart.properties(width=width, height=height).configure_view(
        stroke="#E5E7EB",
        strokeWidth=1,
        fill="#FFFFFF",
    )


# =========================
# PAGE: Landing
# =========================
def landing_page():
    set_landing_style()

    st.markdown(
        """
        <div class="landing-root">
          <div class="landing-icon-wrapper">
            <span class="landing-icon">🏥</span>
          </div>
          <div class="landing-title">
            บริหารเครื่องมือแพทย์อย่างมืออาชีพ เพื่อผลการตรวจที่แม่นยำและ<br>
            ปลอดภัย แบบ <span class="landing-highlight">Real-time</span>
          </div>
          <div class="landing-sub">
            จัดการครุภัณฑ์เครื่องมือแพทย์ ตั้งแต่ทะเบียน ประวัติการใช้งาน การแจ้งซ่อม
            และข้อมูลห้องปฏิบัติการ ให้ทุกคนใช้ข้อมูลชุดเดียวกัน รองรับการตรวจประเมินมาตรฐานต่าง ๆ ได้อย่างมั่นใจ
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ปุ่มอยู่กึ่งกลาง
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown('<div class="landing-buttons-row">', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="landing-btn-outline">', unsafe_allow_html=True)
            start_clicked = st.button("เริ่มใช้งานระบบ", key="btn_start")
            st.markdown("</div>", unsafe_allow_html=True)
        with col_b:
            st.markdown('<div class="landing-btn-primary">', unsafe_allow_html=True)
            login_clicked = st.button("เข้าสู่ระบบ", key="btn_login")
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="landing-note">สำหรับเจ้าหน้าที่ที่ได้รับสิทธิ์ใช้งานห้องปฏิบัติการเท่านั้น</div>',
            unsafe_allow_html=True,
        )

    # ส่วน Feature cards (3 ใบ)
    features_html = """
    <div class="landing-feature-wrapper">
      <div class="landing-feature-row">

        <div class="landing-feature-card">
          <div class="landing-feature-icon-wrapper card-icon-1">
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
            <span class="landing-feature-icon">📱</span>
          </div>
          <div class="landing-feature-title">ตรวจเช็กครุภัณฑ์ด้วยสแกน QR Code</div>
          <div class="landing-feature-text">
            ติด QR ที่อุปกรณ์และสแกนด้วยมือถือ เพื่อเปิดหน้าข้อมูลครุภัณฑ์ แสดงรูป ประวัติ และสถานะการแจ้งซ่อมได้ทันที
          </div>
        </div>

        <div class="landing-feature-card">
          <div class="landing-feature-icon-wrapper card-icon-3">
            <span class="landing-feature-icon">📊</span>
          </div>
          <div class="landing-feature-title">Dashboard สรุปภาพรวมแบบ Real-time</div>
          <div class="landing-feature-text">
            เห็นภาพรวมจำนวนครุภัณฑ์ตามสถานะ ห้องที่มีครุภัณฑ์มากที่สุด และข้อมูลที่ใช้เตรียมเอกสารตรวจประเมินมาตรฐานต่าง ๆ
          </div>
        </div>

      </div>
    </div>
    """
    st.markdown(features_html, unsafe_allow_html=True)

    # ถ้ากดปุ่ม -> ไปหน้า login
    if start_clicked or login_clicked:
        st.session_state.view = "login"
        st.rerun()


# =========================
# PAGE: Login
# =========================
def login_page():
    set_landing_style()
    set_login_background()

    # ให้ container login ใช้ class เฉพาะ (ใช้ hack ง่าย ๆ)
    st.markdown(
        """
        <script>
        const s = window.parent.document.querySelectorAll('.block-container');
        if (s.length > 0) { s[0].classList.add('login-container'); }
        </script>
        """,
        unsafe_allow_html=True,
    )

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
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.display_name = display_name
            st.session_state.view = "app"
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")


# =========================
# PAGE: Dashboard (หน้าหลัก)
# =========================
def page_home():
    set_main_background()

    st.markdown(
        """
        <div class="mem-page-title">หน้าหลัก</div>
        <div class="mem-page-subtitle">
            ภาพรวมการจัดการครุภัณฑ์ และเครื่องมือห้องปฏิบัติการ (ดึงข้อมูลจากไฟล์ Excel ที่เลือกอยู่)
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel ที่เลือกอยู่")
        return

    status_col = "สถานะ"
    if status_col not in df.columns:
        st.warning("ไม่พบคอลัมน์ 'สถานะ' ในไฟล์ Excel")
        return

    # ---------- เตรียมข้อมูลสถานะ ----------
    status_counts = (
        df[status_col]
        .fillna("ไม่ทราบสถานะ")
        .value_counts()
        .rename_axis("สถานะ")
        .reset_index(name="count")
    )

    total = status_counts["count"].sum()
    status_counts["percent"] = status_counts["count"] / max(total, 1)
    status_counts["label_short"] = status_counts.apply(
        lambda r: f"{r['percent']*100:.1f}%", axis=1
    )

    status_order = [
        "พร้อมใช้งาน",
        "ตรวจไม่พบ",
        "ชำรุด(ซ่อมแซมได้)",
        "ชำรุด(ซ่อมแซมไม่ได้)",
        "ไม่ทราบสถานะ",
    ]
    color_map = {
        "พร้อมใช้งาน": "#22c55e",
        "ตรวจไม่พบ": "#9ca3af",
        "ชำรุด(ซ่อมแซมได้)": "#f97316",
        "ชำรุด(ซ่อมแซมไม่ได้)": "#ef4444",
        "ไม่ทราบสถานะ": "#6b7280",
    }
    status_counts["สถานะ"] = pd.Categorical(
        status_counts["สถานะ"], categories=status_order, ordered=True
    )

    alt_color_scale = alt.Scale(
        domain=list(color_map.keys()),
        range=[color_map[k] for k in color_map.keys()],
    )

    # ---------- ข้อมูลตามสถานที่ใช้งาน ----------
    loc_col = "สถานที่ใช้งาน (ปัจจุบัน)"
    loc_total = 0
    top_loc_name = "ไม่พบข้อมูล"
    top_loc_count = 0
    loc_counts = pd.DataFrame(columns=["สถานที่ใช้งาน", "count"])

    if loc_col in df.columns:
        loc_series = df[loc_col].dropna()
        if not loc_series.empty:
            loc_counts = (
                loc_series.value_counts()
                .rename_axis("สถานที่ใช้งาน")
                .reset_index(name="count")
            )
            loc_total = int(loc_counts["สถานที่ใช้งาน"].nunique())
            top_loc_name = str(loc_counts.iloc[0]["สถานที่ใช้งาน"])
            top_loc_count = int(loc_counts.iloc[0]["count"])

    # ---------- SUMMARY ตัวเลข (Hero) ----------
    def get_count(label: str) -> int:
        try:
            return int(status_counts.loc[status_counts["สถานะ"] == label, "count"].sum())
        except Exception:
            return 0

    cnt_total = int(total)
    cnt_ready = get_count("พร้อมใช้งาน")
    cnt_repairable = get_count("ชำรุด(ซ่อมแซมได้)")
    cnt_unrepairable = get_count("ชำรุด(ซ่อมแซมไม่ได้)")
    cnt_missing = get_count("ตรวจไม่พบ")

    legend_items = [
        ("พร้อมใช้งาน", color_map["พร้อมใช้งาน"]),
        ("ตรวจไม่พบ", color_map["ตรวจไม่พบ"]),
        ("ชำรุด (ซ่อมแซมได้)", color_map["ชำรุด(ซ่อมแซมได้)"]),
        ("ชำรุด (ซ่อมแซมไม่ได้)", color_map["ชำรุด(ซ่อมแซมไม่ได้)"]),
        ("ไม่ทราบสถานะ", color_map["ไม่ทราบสถานะ"]),
    ]
    legend_html_parts = []
    for label, color in legend_items:
        legend_html_parts.append(
            f'<div class="mem-status-legend-item">'
            f'<span class="mem-status-dot" style="background:{color};"></span>'
            f'<span>{label}</span>'
            f"</div>"
        )
    legend_html = "".join(legend_html_parts)

    hero_html = (
        '<div class="mem-hero">'
        '<div class="mem-hero-title">จำนวนครุภัณฑ์</div>'
        '<div class="mem-hero-sub">'
        "สรุปจำนวนครุภัณฑ์ทั้งหมด แยกตามสถานะ และจำนวนตามสถานที่ใช้งานจากข้อมูลล่าสุดในระบบ"
        "</div>"
        '<div class="mem-hero-metrics">'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">รวมครุภัณฑ์ทั้งหมด</div>'
        f'<div class="mem-hero-metric-value">{cnt_total}</div>'
        '<span class="mem-hero-metric-pill">ทั้งหมด</span>'
        "</div>"
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">พร้อมใช้งาน</div>'
        f'<div class="mem-hero-metric-value">{cnt_ready}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#dcfce7;color:#166534;">สถานะดี</span>'
        "</div>"
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">ชำรุด (ซ่อมแซมได้)</div>'
        f'<div class="mem-hero-metric-value">{cnt_repairable}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#ffedd5;color:#9a3412;">ต้องซ่อมแซม</span>'
        "</div>"
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">ชำรุด (ซ่อมแซมไม่ได้)</div>'
        f'<div class="mem-hero-metric-value">{cnt_unrepairable}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#fee2e2;color:#991b1b;">พิจารณาจัดหาใหม่</span>'
        "</div>"
        f'<div class="mem-hero-metric">'
        "<div class=\"mem-hero-metric-label\">ตรวจไม่พบ / สูญหาย</div>"
        f'<div class="mem-hero-metric-value">{cnt_missing}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#e5e7eb;color:#111827;">ติดตามตรวจสอบ</span>'
        "</div>"
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">จำนวนสถานที่ใช้งานทั้งหมด</div>'
        f'<div class="mem-hero-metric-value">{loc_total}</div>'
        '<span class="mem-hero-metric-pill">ตามไฟล์ Excel</span>'
        "</div>"
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">สถานที่ที่มีครุภัณฑ์มากที่สุด</div>'
        f'<div class="mem-hero-metric-value" style="font-size:14px;">{top_loc_name}</div>'
        '<span class="mem-hero-metric-pill" '
        f'style="background:#cffafe;color:#0f766e;">{top_loc_count} รายการ</span>'
        "</div>"
        "</div>"
        '<div class="mem-status-legend-wrapper"><div class="mem-status-legend">'
        f"{legend_html}"
        "</div></div>"
        "</div>"
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # ---------- Pie + ตาราง ----------
    base_pie = (
        alt.Chart(status_counts)
        .encode(
            theta=alt.Theta("count:Q", stack=True),
            color=alt.Color("สถานะ:N", scale=alt_color_scale, legend=alt.Legend(title="สถานะ")),
            tooltip=[
                alt.Tooltip("สถานะ:N", title="สถานะ"),
                alt.Tooltip("count:Q", title="จำนวน"),
                alt.Tooltip("percent:Q", title="สัดส่วน", format=".1%"),
            ],
        )
    )

    pie = base_pie.mark_arc(
        outerRadius=150,
        innerRadius=70,
        stroke="white",
        strokeWidth=2,
    )

    labels = base_pie.mark_text(radius=110, size=13, color="#111827", fontWeight="bold").encode(
        text="label_short:N"
    )

    pie_chart = styled_chart(pie + labels, width=420, height=320)

    status_table_df = status_counts.sort_values("สถานะ").copy()
    status_table_df = status_table_df[["สถานะ", "count"]]
    status_table_df.rename(columns={"count": "จำนวน (รายการ)"}, inplace=True)

    st.markdown(
        """
        <div class="mem-card">
          <div class="mem-card-title">สัดส่วนตามสถานะครุภัณฑ์</div>
          <div class="mem-card-subtitle">
            แสดงสัดส่วนและจำนวนครุภัณฑ์แต่ละสถานะ ช่วยให้เห็นภาพรวมความพร้อมใช้งานของครุภัณฑ์ทั้งหมด
          </div>
        """,
        unsafe_allow_html=True,
    )

    col_pie, col_table = st.columns([1, 1])
    with col_pie:
        st.altair_chart(pie_chart, use_container_width=True)
    with col_table:
        st.dataframe(
            status_table_df,
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Hero card 2: Top Location ----------
    if not loc_counts.empty:
        metric_parts = []
        for rank, (_, r) in enumerate(loc_counts.head(6).iterrows(), start=1):
            name = str(r["สถานที่ใช้งาน"])
            cnt = int(r["count"])
            metric_parts.append(
                '<div class="mem-hero-metric">'
                f'<div class="mem-hero-metric-label">{name}</div>'
                f'<div class="mem-hero-metric-value">{cnt}</div>'
                f'<span class="mem-hero-metric-pill">อันดับ {rank}</span>'
                "</div>"
            )

        loc_hero_html = (
            '<div class="mem-hero">'
            '<div class="mem-hero-title">สถานที่ที่มีครุภัณฑ์ในระบบ</div>'
            '<div class="mem-hero-sub">'
            "แสดงอันดับสถานที่ที่มีจำนวนครุภัณฑ์มากที่สุด จากข้อมูลในตารางรายการครุภัณฑ์ปัจจุบัน"
            "</div>"
            '<div class="mem-hero-metrics">'
            + "".join(metric_parts)
            + "</div></div>"
        )
        st.markdown(loc_hero_html, unsafe_allow_html=True)


# =========================
# Helper: ตาราง + เลือกแถว
# =========================
def equipment_table_with_selection(df: pd.DataFrame):
    df_with_sel = df.copy()
    if "เลือก" not in df_with_sel.columns:
        df_with_sel.insert(0, "เลือก", False)

    edited_df = st.data_editor(
        df_with_sel,
        key="equip_table",
        use_container_width=True,
        height=280,
        hide_index=True,
        column_config={
            "เลือก": st.column_config.CheckboxColumn(
                "เลือก", help="ติ๊กเลือกครุภัณฑ์เพื่อใช้สำหรับลบหลายรายการ"
            )
        },
        disabled=[c for c in df_with_sel.columns if c != "เลือก"],
    )

    selected_rows = edited_df[edited_df["เลือก"]].index.tolist()
    st.session_state["rows_for_delete"] = selected_rows


# =========================
# PAGE: รายการครุภัณฑ์ + ฟอร์มแก้ไข
# =========================
def page_equipment_list():
    set_main_background()

    st.markdown(
        '<div class="mem-page-title">รายการครุภัณฑ์</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### เลือกไฟล์ Excel ที่ต้องการใช้งาน")

    files = get_available_excel_files()
    init_excel_file_name()
    current_name = st.session_state.get("excel_file_name")

    if not files and not DEFAULT_EXCEL_PATH.exists():
        st.info("ยังไม่มีไฟล์ Excel ในโฟลเดอร์ data กรุณาอัปโหลดไฟล์ใหม่")
    else:
        if current_name not in files and DEFAULT_EXCEL_PATH.exists():
            current_name = DEFAULT_EXCEL_NAME
            st.session_state["excel_file_name"] = current_name
        elif current_name not in files and files:
            current_name = files[0]
            st.session_state["excel_file_name"] = current_name

        if files:
            idx_default = files.index(current_name)
            selected_file = st.selectbox(
                "ไฟล์สำหรับใช้งาน",
                options=files,
                index=idx_default,
                key="excel_select",
            )

            col_use, col_path = st.columns([1, 1])
            with col_use:
                if st.button("ใช้ไฟล์นี้", key="btn_use_excel", use_container_width=True):
                    st.session_state["excel_file_name"] = selected_file
                    st.success(f"กำลังใช้งานไฟล์: {selected_file}")
                    st.rerun()
            with col_path:
                path = DATA_DIR / current_name
                st.caption(
                    f"ไฟล์ที่ใช้งานอยู่: **{current_name}**\n\nที่อยู่ไฟล์: `{path}`"
                )

    # อัปโหลดไฟล์ใหม่
    with st.expander("📁 อัปโหลดไฟล์ Excel ใหม่ (เพิ่ม/แทนที่ไฟล์เดิม)", expanded=False):
        uploaded = st.file_uploader("เลือกไฟล์ Excel", type=["xlsx", "xls"])
        if uploaded is not None:
            save_path = DATA_DIR / uploaded.name
            try:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"บันทึกไฟล์ {uploaded.name} ลงโฟลเดอร์ data แล้ว")

                st.session_state["excel_file_name"] = uploaded.name
                st.rerun()
            except Exception as e:
                st.error(f"ไม่สามารถบันทึกไฟล์ได้: {e}")

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลในไฟล์ Excel ที่เลือกอยู่")
        return

    st.markdown("### ตารางรายการครุภัณฑ์")
    equipment_table_with_selection(df)

    # ----- ปุ่มลบ -----
    st.markdown("#### จัดการลบข้อมูล")
    col_del1, col_del2 = st.columns([1, 1.2])

    with col_del1:
        if st.button("🗑️ ลบรายการที่เลือก", use_container_width=True):
            rows = st.session_state.get("rows_for_delete", [])
            if not rows:
                st.warning("กรุณาติ๊กเลือกอย่างน้อย 1 รายการในคอลัมน์ 'เลือก' ก่อนลบ")
            else:
                df_new = df.drop(index=rows).reset_index(drop=True)
                save_equipment_data(df_new)
                st.session_state["selected_row_idx"] = 0
                st.rerun()

    with col_del2:
        confirm_all = st.checkbox(
            "ยืนยันการลบข้อมูลทั้งหมดในตาราง", key="confirm_delete_all"
        )
        if st.button("🧹 ลบข้อมูลทั้งหมด", use_container_width=True):
            if not confirm_all:
                st.warning("กรุณาติ๊ก 'ยืนยันการลบข้อมูลทั้งหมดในตาราง' ก่อนลบทั้งหมด")
            else:
                df_new = df.iloc[0:0]
                save_equipment_data(df_new)
                st.session_state["selected_row_idx"] = 0
                st.rerun()

    # ----- เลือกแถวสำหรับแก้ไข -----
    def format_option(i: int) -> str:
        row = df.iloc[i]
        name = str(row.get("ชื่อ", "ไม่ทราบชื่อ"))
        code = str(row.get(ASSET_CODE_COL, ""))
        return f"{i+1:03d} - {name} ({code})"

    options_index = list(df.index)
    default_idx = st.session_state.get("selected_row_idx", 0)
    if default_idx >= len(df):
        default_idx = 0

    selected_idx_box = st.selectbox(
        "เลือกครุภัณฑ์สำหรับดู/แก้ไขรายละเอียด",
        options=options_index,
        index=default_idx,
        format_func=format_option,
        key="equip_select_box_admin",
    )

    if selected_idx_box != st.session_state.get("selected_row_idx", 0):
        st.session_state.selected_row_idx = selected_idx_box
        st.rerun()

    selected_idx = st.session_state.get("selected_row_idx", 0)

    st.markdown("### รายละเอียดครุภัณฑ์")
    st.markdown("#### ฟอร์มรายละเอียด", unsafe_allow_html=True)

    if len(df) == 0:
        st.info("ยังไม่มีข้อมูลให้แสดง")
        return

    row = df.iloc[selected_idx].copy()
    asset_code = str(row.get(ASSET_CODE_COL, ""))

    # ---- ฟิลด์หลัก (ยกเว้นคอลัมน์ภาพ/สถานะแจ้งซ่อม/บันทึกหน้างาน) ----
    columns_list = [
        c
        for c in df.columns
        if c not in ("รูปภาพครุภัณฑ์", "สถานะแจ้งซ่อม", "บันทึกจากหน้างานล่าสุด")
    ]
    half = (len(columns_list) + 1) // 2
    left_cols = columns_list[:half]
    right_cols = columns_list[half:]

    col_left, col_right = st.columns(2)
    updated_values: dict[str, str] = {}

    with col_left:
        for col_name in left_cols:
            current_val = row.get(col_name, "")
            new_val = st.text_input(
                str(col_name),
                value="" if pd.isna(current_val) else str(current_val),
                key=f"detail_left_{col_name}_{selected_idx}",
            )
            updated_values[col_name] = new_val

    with col_right:
        for col_name in right_cols:
            current_val = row.get(col_name, "")
            new_val = st.text_input(
                str(col_name),
                value="" if pd.isna(current_val) else str(current_val),
                key=f"detail_right_{col_name}_{selected_idx}",
            )
            updated_values[col_name] = new_val

    # ---- ส่วนสถานะแจ้งซ่อม + note ----
    st.markdown("### สถานะแจ้งซ่อม")
    current_maint = str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or "")
    if current_maint not in MAINT_STATUS_CHOICES:
        current_maint = MAINT_STATUS_CHOICES[0]

    maint_select = st.selectbox(
        "สถานะแจ้งซ่อม",
        MAINT_STATUS_CHOICES,
        index=MAINT_STATUS_CHOICES.index(current_maint),
        key=f"maint_status_admin_{selected_idx}",
    )
    updated_values["สถานะแจ้งซ่อม"] = maint_select

    current_note = str(row.get("บันทึกจากหน้างานล่าสุด", "") or "")
    updated_note = st.text_area(
        "บันทึกจากหน้างานล่าสุด (จากหน้างาน / QR)",
        value=current_note,
        key=f"note_admin_{selected_idx}",
        height=80,
    )
    updated_values["บันทึกจากหน้างานล่าสุด"] = updated_note

    # ---- QR + รูปภาพ ----
    st.markdown("### QR Code และรูปภาพครุภัณฑ์")
    qr_col, img_col = st.columns([1, 1])

    with qr_col:
        st.subheader("QR Code ของครุภัณฑ์")
        qr_path = get_qr_image_path_from_row(row)
        qr_bytes_for_download = None

        if qr_path and qr_path.exists():
            st.image(str(qr_path), use_column_width=True)
            with open(qr_path, "rb") as f:
                qr_bytes_for_download = f.read()
        else:
            url_for_qr = (
                "https://memsystemdashboard-qr.streamlit.app/"
                f"?code={asset_code}"
            )
            qr_bytes_for_download = generate_qr_bytes_for_url(url_for_qr)
            st.image(qr_bytes_for_download, use_column_width=True)

        st.caption(asset_code)
        st.write("สแกน QR นี้เพื่อเปิดหน้าข้อมูลครุภัณฑ์จากอุปกรณ์อื่น ๆ ได้เช่นกัน")

        if qr_bytes_for_download:
            st.download_button(
                "⬇️ ดาวน์โหลด QR (PNG)",
                data=qr_bytes_for_download,
                file_name=f"{asset_code}_qr.png",
                mime="image/png",
                use_container_width=True,
            )

    with img_col:
        st.subheader("รูปภาพครุภัณฑ์")
        current_img_path = get_image_path_from_row(row)
        if current_img_path and current_img_path.exists():
            st.image(str(current_img_path), caption="รูปภาพปัจจุบัน", use_column_width=True)
        else:
            st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")

        uploaded_img = st.file_uploader(
            "อัปโหลดรูปภาพใหม่ (ถ้าไม่เลือก ระบบจะใช้ของเดิม)",
            type=["png", "jpg", "jpeg"],
            key=f"upload_image_admin_{selected_idx}",
        )

    st.write("")
    if st.button("บันทึกการแก้ไข", type="primary", use_container_width=True):
        df_current = load_equipment_data()
        if selected_idx >= len(df_current):
            st.error("แถวข้อมูลนี้ไม่อยู่ในตารางแล้ว กรุณารีเฟรชหน้าเว็บ")
            return

        for col in updated_values:
            if col not in df_current.columns:
                continue
            raw_val = updated_values.get(col, "")
            orig_dtype = df_current[col].dtype

            if pd.api.types.is_numeric_dtype(orig_dtype):
                if raw_val == "":
                    df_current.at[selected_idx, col] = pd.NA
                else:
                    try:
                        df_current.at[selected_idx, col] = pd.to_numeric(raw_val)
                    except Exception:
                        df_current.at[selected_idx, col] = raw_val
            else:
                df_current.at[selected_idx, col] = raw_val

        if uploaded_img is not None:
            filename = save_uploaded_image(uploaded_img, asset_code)
            if "รูปภาพครุภัณฑ์" not in df_current.columns:
                df_current["รูปภาพครุภัณฑ์"] = ""
            df_current.at[selected_idx, "รูปภาพครุภัณฑ์"] = filename

        save_equipment_data(df_current)
        st.rerun()


# =========================
# PAGE: แจ้งซ่อม / บำรุงรักษา
# =========================
def page_maintenance():
    set_main_background()

    st.markdown(
        '<div class="mem-page-title">แจ้งซ่อม / บำรุงรักษา</div>',
        unsafe_allow_html=True,
    )

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel ที่เลือกอยู่")
        return

    if "สถานะแจ้งซ่อม" not in df.columns:
        st.warning("ไม่พบคอลัมน์ 'สถานะแจ้งซ่อม' ในไฟล์ Excel")
        return

    maint_counts = (
        df["สถานะแจ้งซ่อม"]
        .fillna(MAINT_STATUS_CHOICES[0])
        .value_counts()
        .rename_axis("สถานะแจ้งซ่อม")
        .reset_index(name="count")
    )

    st.markdown(
        """
        <div class="mem-card">
          <div class="mem-card-title">ภาพรวมสถานะแจ้งซ่อม</div>
          <div class="mem-card-subtitle">
            แสดงจำนวนครุภัณฑ์ตามสถานะแจ้งซ่อม เพื่อช่วยติดตามงานซ่อมบำรุง
          </div>
        """,
        unsafe_allow_html=True,
    )

    chart = (
        alt.Chart(maint_counts)
        .mark_bar()
        .encode(
            x=alt.X("สถานะแจ้งซ่อม:N", sort=None, title="สถานะแจ้งซ่อม"),
            y=alt.Y("count:Q", title="จำนวน (รายการ)"),
            tooltip=["สถานะแจ้งซ่อม:N", "count:Q"],
        )
    )
    chart = styled_chart(chart, width=500, height=320)
    st.altair_chart(chart, use_container_width=True)

    st.dataframe(
        maint_counts.rename(columns={"count": "จำนวน (รายการ)"}),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# PAGE: รายงานสรุป
# =========================
def page_summary():
    set_main_background()
    st.markdown(
        '<div class="mem-page-title">รายงานสรุป</div>',
        unsafe_allow_html=True,
    )
    st.info("ส่วนนี้ใช้ทำรายงานสรุปครุภัณฑ์ / วิเคราะห์ข้อมูลเพิ่มเติมในอนาคต")


# =========================
# MAIN APP หลัง Login
# =========================
def main_app():
    set_main_background()

    with st.sidebar:
        st.markdown(
            f"""
            <div class="mem-sidebar-user">
              <div style="font-size:28px; font-weight:700; margin-bottom:4px;">AD</div>
              <div class="mem-sidebar-user-name">{st.session_state.get('display_name', 'admin')}</div>
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
            st.session_state.clear()
            st.session_state.logged_in = False
            st.session_state.view = "landing"
            st.rerun()

    menu = st.session_state.get("current_menu", "หน้าหลัก")

    if menu == "หน้าหลัก":
        page_home()
    elif menu == "รายการครุภัณฑ์":
        page_equipment_list()
    elif menu == "แจ้งซ่อม / บำรุงรักษา":
        page_maintenance()
    elif menu == "รายงานสรุป":
        page_summary()


# =========================
# ENTRY POINT (Login session ค้างถึงจะกด Logout)
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "หน้าหลัก"
if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = 0

if st.session_state.logged_in:
    # ถ้าล็อกอินแล้ว ต่อให้ Refresh ก็ยังอยู่ใน main_app()
    main_app()
else:
    if st.session_state.view == "login":
        login_page()
    else:
        landing_page()
