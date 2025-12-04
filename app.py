# app.py
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, get_excel_path
from auth import authenticate_user, login_user, logout_user, is_logged_in

# =========================
# CONFIG / CONSTANTS
# =========================
ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"

IMAGE_DIR = Path("asset_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

QR_IMAGES_DIR = Path("qr_images")
QR_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

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
            max-width: 1000px;
            margin: 3.2rem auto 3rem auto;
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
            font-size:34px;
            font-weight:800;
            line-height:1.3;
            color:#020617;
            margin-bottom:0.9rem;
        }
        .landing-highlight{
            color:#2563eb;
        }
        .landing-sub{
            font-size:13px;
            color:#6b7280;
            max-width:680px;
            margin:0 auto 1.9rem auto;
        }
        .landing-btn-group{
            display:flex;
            justify-content:center;
            gap:12px;
            margin-bottom:0.5rem;
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
        .landing-btn-primary button:hover{
            background:#1d4ed8;
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
        .landing-note{
            margin-top:0.55rem;
            font-size:11px;
            color:#9ca3af;
        }

        .landing-feature-wrapper{
            max-width:1050px;
            margin:2.2rem auto 2.8rem auto;
        }
        .landing-feature-row{
            display:flex;
            flex-wrap:wrap;
            gap:18px;
            justify-content:center;
        }
        .landing-feature-card{
            background:#ffffff;
            border-radius:28px;
            padding:22px 22px 18px 22px;
            box-shadow:0 14px 40px rgba(15,23,42,0.16);
            border:1px solid rgba(209,213,219,0.7);
            width:300px;
        }
        .landing-feature-icon-wrapper{
            width:46px;
            height:46px;
            border-radius:18px;
            background:#fef9c3;
            display:flex;
            align-items:center;
            justify-content:center;
            margin-bottom:10px;
        }
        .card-icon-1{
            background:#fef9c3;
        }
        .card-icon-2{
            background:#fee2e2;
        }
        .card-icon-3{
            background:#dbeafe;
        }
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

        .stTextInput > div > div > input{
            border-radius: 999px;
            border: none;
            background: transparent;
            outline: none;
            color: #111827;
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

        /* SIDEBAR */
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

        .mem-card{
            background: #FFFFFF;
            border-radius: 32px;
            padding: 20px 24px 24px 24px;
            margin-bottom: 26px;
            box-shadow: 0 22px 52px rgba(15,23,42,0.08);
            border: 2px solid rgba(148,163,184,0.45);
            position: relative;
            overflow: hidden;
        }
        .mem-card::before{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            height: 5px;
            border-radius: 30px 30px 0 0;
            background: linear-gradient(90deg,#22c55e,#0ea5e9,#6366f1);
        }
        .mem-card-title{
            font-size: 18px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.6rem;
        }
        .mem-card-subtitle{
            font-size: 12px;
            color: #9CA3AF;
            margin-bottom: 0.6rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# Excel helpers (ใช้ร่วมกัน)
# =========================
def load_equipment_data() -> pd.DataFrame:
    """อ่านข้อมูลจากไฟล์ Excel กลาง"""
    path = get_excel_path()
    if not path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)

        # เตรียม column ที่ใช้ในระบบให้มีแน่ๆ
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
    """บันทึกข้อมูลลงไฟล์ Excel แบบปลอดภัย (เขียน temp แล้วค่อยแทนที่)"""
    path = get_excel_path()
    if path is None:
        st.error("ยังไม่ได้กำหนดไฟล์ Excel สำหรับบันทึกข้อมูล")
        return

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")

        df.to_excel(tmp_path, index=False)
        tmp_path.replace(path)

        st.success(f"บันทึกการแก้ไขลงไฟล์: {path.name} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")

# =========================
# รูป & QR helpers
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
            จัดการครุภัณฑ์เครื่องมือแพทย์ตั้งแต่ทะเบียน ประวัติการใช้งาน การแจ้งซ่อม 
            และข้อมูลห้องปฏิบัติการ ให้ทุกคนในทีมใช้ข้อมูลชุดเดียวกัน 
            รองรับการตรวจประเมินคุณภาพมาตรฐานต่าง ๆ ได้อย่างมั่นใจ
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-btn-group">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="landing-btn-outline">', unsafe_allow_html=True)
        start_btn = st.button("เริ่มใช้งานระบบ", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="landing-btn-primary">', unsafe_allow_html=True)
        login_btn = st.button("เข้าสู่ระบบ", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="landing-note">สำหรับเจ้าหน้าที่ที่ได้รับสิทธิ์ใช้งานห้องปฏิบัติการเท่านั้น</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)  # ปิด landing-container

    # Feature cards
    st.markdown('<div class="landing-feature-wrapper">', unsafe_allow_html=True)
    st.markdown(
        """
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
              <span class="landing-feature-icon">🔳</span>
            </div>
            <div class="landing-feature-title">ตรวจเช็กครุภัณฑ์หน้างานด้วย QR Code</div>
            <div class="landing-feature-text">
              ติด QR ที่อุปกรณ์และสแกนด้วยมือถือ เพื่อเปิดหน้าข้อมูลครุภัณฑ์ แสดงรูป ประวัติ 
              และสถานะการแจ้งซ่อมได้ทันที
            </div>
          </div>

          <div class="landing-feature-card">
            <div class="landing-feature-icon-wrapper card-icon-3">
              <span class="landing-feature-icon">📊</span>
            </div>
            <div class="landing-feature-title">Dashboard สรุปภาพรวมแบบ Real-time</div>
            <div class="landing-feature-text">
              เห็นจำนวนครุภัณฑ์แต่ละสถานะ ห้องที่มีครุภัณฑ์มากที่สุด และข้อมูลที่ใช้เตรียมเอกสาร
              สำหรับการตรวจประเมินมาตรฐานต่าง ๆ
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # กดปุ่ม → ไปหน้า login
    if start_btn or login_btn:
        st.session_state.view = "login"
        st.rerun()

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
            login_user(username, display_name)
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")

# =========================
# Helper: chart style
# =========================
def styled_chart(chart: alt.Chart, width: int, height: int) -> alt.Chart:
    return (
        chart.properties(width=width, height=height)
        .configure_view(
            stroke="#E5E7EB",
            strokeWidth=1,
            fill="#FFFFFF",
        )
    )

# =========================
# หน้า Dashboard / หน้าหลัก
# =========================
def page_home():
    set_main_style()
    st.markdown(
        """
        <div>
            <div class="mem-page-title">หน้าหลัก</div>
            <div class="mem-page-subtitle">
                ภาพรวมการจัดการครุภัณฑ์ และเครื่องมือห้องปฏิบัติการ (ดึงข้อมูลจากไฟล์ Excel กลาง)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel กลาง")
        return

    status_col = "สถานะ"
    if status_col not in df.columns:
        st.warning("ไม่พบคอลัมน์ 'สถานะ' ในไฟล์ Excel")
        return

    # เตรียมข้อมูลสถานะ
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

    # hero metric
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

    hero_html = f"""
    <div class="mem-card">
      <div class="mem-card-title">สรุปจำนวนครุภัณฑ์</div>
      <div class="mem-card-subtitle">
        แสดงจำนวนครุภัณฑ์แยกตามสถานะ จากข้อมูลปัจจุบันในไฟล์ Excel กลาง
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:10px;">
        <div class="mem-hero-metric">
          <div class="mem-hero-metric-label">รวมครุภัณฑ์ทั้งหมด</div>
          <div class="mem-hero-metric-value">{cnt_total}</div>
        </div>
        <div class="mem-hero-metric">
          <div class="mem-hero-metric-label">พร้อมใช้งาน</div>
          <div class="mem-hero-metric-value">{cnt_ready}</div>
        </div>
        <div class="mem-hero-metric">
          <div class="mem-hero-metric-label">ชำรุด (ซ่อมแซมได้)</div>
          <div class="mem-hero-metric-value">{cnt_repairable}</div>
        </div>
        <div class="mem-hero-metric">
          <div class="mem-hero-metric-label">ชำรุด (ซ่อมแซมไม่ได้)</div>
          <div class="mem-hero-metric-value">{cnt_unrepairable}</div>
        </div>
        <div class="mem-hero-metric">
          <div class="mem-hero-metric-label">ตรวจไม่พบ / สูญหาย</div>
          <div class="mem-hero-metric-value">{cnt_missing}</div>
        </div>
      </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)

    # donut chart
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
    pie = base_pie.mark_arc(outerRadius=150, innerRadius=70, stroke="white", strokeWidth=2)
    labels = (
        base_pie.mark_text(radius=110, size=13, color="#111827", fontWeight="bold")
        .encode(text="label_short:N")
    )
    pie_chart = styled_chart(pie + labels, width=420, height=320)

    status_table_df = status_counts.sort_values("สถานะ").copy()
    status_table_df = status_table_df[["สถานะ", "count"]]
    status_table_df.rename(columns={"count": "จำนวน (รายการ)"}, inplace=True)

    st.markdown('<div class="mem-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="mem-card-title">สัดส่วนตามสถานะครุภัณฑ์</div>'
        '<div class="mem-card-subtitle">'
        'ช่วยให้เห็นภาพรวมความพร้อมใช้งานของครุภัณฑ์ในระบบ'
        '</div>',
        unsafe_allow_html=True,
    )
    col_pie, col_table = st.columns([1, 1])
    with col_pie:
        st.altair_chart(pie_chart, use_container_width=True)
    with col_table:
        st.dataframe(status_table_df, hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Helper: ตาราง + เลือกแถวในหน้า "รายการครุภัณฑ์"
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
# หน้า "รายการครุภัณฑ์"
# =========================
def page_equipment_list():
    set_main_style()
    st.markdown('<div class="mem-page-title">รายการครุภัณฑ์</div>', unsafe_allow_html=True)

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลในไฟล์ Excel กลาง")
        return

    st.markdown("### ตารางรายการครุภัณฑ์")
    equipment_table_with_selection(df)

    # ปุ่มลบ
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

    # เลือกแถวสำหรับแก้ไขรายละเอียด
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
    if len(df) == 0:
        st.info("ยังไม่มีข้อมูลให้แสดง")
        return

    row = df.iloc[selected_idx].copy()
    asset_code = str(row.get(ASSET_CODE_COL, ""))

    # ฟิลด์หลัก (ยกเว้น สถานะแจ้งซ่อม + รูปภาพครุภัณฑ์)
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

    # สถานะแจ้งซ่อม
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

    # QR + รูปภาพ
    st.markdown("### QR Code และรูปภาพครุภัณฑ์")
    qr_col, img_col = st.columns([1, 1])

    with qr_col:
        st.subheader("QR Code ของครุภัณฑ์")
        url_for_qr = f"https://memsystemdashboard-qr.streamlit.app/?code={asset_code}"
        qr_bytes = generate_qr_bytes_for_url(url_for_qr)
        st.image(qr_bytes, use_column_width=True)
        st.caption(asset_code)
        st.download_button(
            "⬇️ ดาวน์โหลด QR (PNG)",
            data=qr_bytes,
            file_name=f"{asset_code}_qr.png",
            mime="image/png",
            use_container_width=True,
        )
        st.write("สแกน QR นี้เพื่อเปิดหน้าข้อมูลครุภัณฑ์จากอุปกรณ์อื่น ๆ ได้เช่นกัน")

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

    # บันทึก
    if st.button("บันทึกการแก้ไข", type="primary"):
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
# หน้า "แจ้งซ่อม / บำรุงรักษา" (ดูสรุปสถานะแจ้งซ่อม)
# =========================
def page_maintenance():
    set_main_style()
    st.markdown(
        '<div class="mem-page-title">แจ้งซ่อม / บำรุงรักษา</div>',
        unsafe_allow_html=True,
    )

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel กลาง")
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
# หน้า "รายงานสรุป"
# =========================
def page_summary():
    set_main_style()
    st.markdown('<div class="mem-page-title">รายงานสรุป</div>', unsafe_allow_html=True)
    st.info("ส่วนนี้ใช้ทำรายงานสรุปครุภัณฑ์ / วิเคราะห์ข้อมูลเพิ่มเติมในอนาคต")

# =========================
# MAIN APP หลัง Login
# =========================
def main_app():
    set_main_style()

    with st.sidebar:
        st.markdown(
            f"""
            <div class="mem-sidebar-user">
              <div style="font-size:28px; font-weight:700; margin-bottom:4px;">AD</div>
              <div class="mem-sidebar-user-name">
                {st.session_state.get('display_name', 'admin')}
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
            logout_user()
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
# ENTRY POINT
# =========================
if "view" not in st.session_state:
    st.session_state.view = "landing"

# ถ้า logged_in อยู่แล้ว รีเฟรชซ้ำ ๆ จะยังอยู่ใน main_app (จนกว่าจะ Logout)
if is_logged_in():
    main_app()
else:
    if st.session_state.view == "login":
        login_page()
    else:
        landing_page()
