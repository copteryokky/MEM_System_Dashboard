import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from io import BytesIO
import qrcode
import calendar
from datetime import datetime

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH
import auth  # ใช้ฟังก์ชันจาก auth.py

# =========================
# Helper: Auth wrapper
# =========================
def auth_login(username: str, password: str):
    """
    ห่อ authenticate_user ให้รองรับหลายรูปแบบ return:
    - True/False
    - (ok, display_name)
    - (ok, display_name, role)
    """
    try:
        result = auth.authenticate_user(username, password)
    except Exception as e:
        st.error(
            "ไม่สามารถตรวจสอบสิทธิ์ผ่านระบบผู้ดูแล (auth.py) ได้\n"
            "กรุณาตรวจสอบไฟล์ auth.py หรือให้ผู้ดูแลระบบช่วยเช็ค"
        )
        return False, username, "user"

    ok = False
    display_name = username
    role = "user"

    if isinstance(result, tuple):
        if len(result) >= 1:
            ok = bool(result[0])
        if len(result) >= 2 and result[1] is not None:
            display_name = str(result[1])
        if len(result) >= 3 and result[2] is not None:
            role = str(result[2])
    else:
        ok = bool(result)

    if username.lower() == "admin" and role == "user":
        # เผื่อ auth.py ไม่ได้ส่ง role มา แต่ล็อกอินด้วย admin
        role = "admin"

    return ok, display_name, role


def auth_register(username: str, password: str, full_name: str, email: str | None = None):
    """
    ห่อ register_user ให้รองรับหลาย signature:
    - register_user(username, password)
    - register_user(username, password, full_name)
    - register_user(username, password, full_name, email)
    ให้ผลลัพธ์เป็น (ok: bool, msg: str)
    """
    try:
        # พยายามเรียกรูปแบบเต็มก่อน
        try:
            result = auth.register_user(username, password, full_name, email)
        except TypeError:
            try:
                result = auth.register_user(username, password, full_name)
            except TypeError:
                result = auth.register_user(username, password)
    except Exception:
        return False, "ไม่สามารถเรียกใช้ฟังก์ชัน register_user ใน auth.py ได้"

    ok = False
    msg = "ไม่ทราบผลการสมัคร"

    if isinstance(result, tuple):
        if len(result) >= 1:
            ok = bool(result[0])
        if len(result) >= 2 and result[1] is not None:
            msg = str(result[1])
    else:
        ok = bool(result)
        msg = "สมัครสมาชิกสำเร็จ" if ok else "สมัครสมาชิกไม่สำเร็จ"

    return ok, msg


def is_admin() -> bool:
    """คืนค่า True ถ้าผู้ใช้ปัจจุบันเป็น admin"""
    # ลองถามจาก auth.py ก่อน
    try:
        return bool(auth.is_admin())
    except Exception:
        return st.session_state.get("current_role", "user") == "admin"


# =========================
# CONFIG พื้นฐาน
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

# ---- คอลัมน์ที่ใช้สำหรับระบบแจ้งซ่อม ----
MAINT_REQUEST_DATE_COL = "วันที่แจ้งซ่อมล่าสุด"
MAINT_EST_DAYS_COL = "ระยะเวลาซ่อมที่กำหนด (วัน)"
MAINT_DUE_DATE_COL = "กำหนดซ่อมเสร็จภายใน"
MAINT_EVAL_COL = "ผลการประเมินการซ่อม"
MAINT_NOTE_COL = "หมายเหตุการซ่อม"  # ช่อง “ทำไมต้องซ่อม / หมายเหตุแจ้งซ่อม”

MAINT_EVAL_CHOICES = [
    "ยังไม่ประเมิน",
    "ซ่อมได้ - อยู่ระหว่างดำเนินการ",
    "ซ่อมไม่ได้ - เสนอปลดระวาง/ทดแทน",
]

# ---- CONFIG สำหรับแผนสอบเทียบ ----
CAL_PLAN_SIMPLE_NAME = "calibration_plan_simple.xlsx"
CAL_PLAN_SIMPLE_PATH = DATA_DIR / CAL_PLAN_SIMPLE_NAME
CAL_ORIGINAL_NAME = "แผนสอบเทียบและบำรุงรักษาเครื่องมือ.xlsx"

# =========================
# STYLE: Landing
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
        .landing-wrapper{
            max-width: 1100px;
            margin: 2.5rem auto 3.2rem auto;
            text-align: center;
        }
        .landing-hero-icon{
            width: 90px;
            height: 90px;
            border-radius: 32px;
            margin: 0 auto 1.4rem auto;
            background: linear-gradient(135deg,#fed7aa,#fecaca);
            display:flex;
            align-items:center;
            justify-content:center;
            box-shadow:0 20px 40px rgba(248,113,113,0.45);
        }
        .landing-hero-icon span{
            width: 64px;
            height: 64px;
            border-radius: 24px;
            background:#fef3c7;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:34px;
        }
        .landing-title{
            font-size:34px;
            font-weight:800;
            line-height:1.25;
            color:#0f172a;
            margin-bottom:0.7rem;
        }
        .landing-title-highlight{
            color:#2563eb;
        }
        .landing-subtitle{
            font-size:14px;
            color:#6b7280;
            max-width:640px;
            margin:0 auto 1.9rem auto;
        }
        .landing-buttons{
            display:flex;
            justify-content:center;
            gap:14px;
            margin-bottom:1.6rem;
            flex-wrap:wrap;
        }
        .landing-note{
            font-size:11px;
            color:#9ca3af;
            margin-bottom:2.0rem;
        }

        .landing-buttons .stButton>button{
            border-radius:999px;
            min-width:180px;
            height:2.8rem;
            font-weight:600;
            font-size:14px;
            border:none;
            box-shadow:0 14px 30px rgba(15,23,42,0.12);
        }
        .btn-outline .stButton>button{
            background:white;
            color:#111827;
            border:1px solid #e5e7eb;
        }
        .btn-outline .stButton>button:hover{
            background:#f3f4f6;
        }
        .btn-primary .stButton>button{
            background:#f97316;
            color:white;
        }
        .btn-primary .stButton>button:hover{
            background:#ea580c;
        }

        .feature-row{
            max-width:1100px;
            margin:0 auto 2.8rem auto;
            display:flex;
            flex-wrap:wrap;
            gap:18px;
            justify-content:center;
        }
        .feature-card{
            flex:1 1 0;
            min-width:230px;
            max-width:320px;
            background:#ffffff;
            border-radius:26px;
            padding:20px 22px 22px 22px;
            box-shadow:0 22px 50px rgba(15,23,42,0.16);
            border:1px solid #e5e7eb;
            text-align:left;
        }
        .feature-icon{
            width:48px;
            height:48px;
            border-radius:18px;
            background:#fef3c7;
            display:flex;
            align-items:center;
            justify-content:center;
            margin-bottom:0.8rem;
            font-size:24px;
        }
        .feature-title{
            font-size:15px;
            font-weight:700;
            color:#111827;
            margin-bottom:0.25rem;
        }
        .feature-text{
            font-size:12px;
            color:#6b7280;
        }

        @media (max-width: 900px){
            .landing-title{font-size:26px;}
            .landing-wrapper{margin-top:1.8rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# STYLE: Login
# =========================
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
            margin: 3.5rem auto 3rem auto;
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


# =========================
# STYLE: Main app
# =========================
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
        .mem-hero{
            background: linear-gradient(135deg,#eef2ff,#e0f2fe);
            border-radius: 26px;
            padding: 18px 26px 16px 26px;
            color: #0f172a;
            box-shadow: 0 18px 40px rgba(15,23,42,0.18);
            margin-bottom: 22px;
            border: 1px solid #dbeafe;
        }
        .mem-hero-title{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .mem-hero-sub{
            font-size: 13px;
            opacity: 0.92;
            margin-bottom: 14px;
        }
        .mem-hero-metrics{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .mem-hero-metric{
            background: #ffffff;
            border-radius: 18px;
            padding: 8px 12px;
            min-width: 165px;
            display: flex;
            flex-direction: column;
        }
        .mem-hero-metric-label{
            font-size: 11px;
            color: #6b7280;
        }
        .mem-hero-metric-value{
            font-size: 18px;
            font-weight: 700;
            line-height: 1.1;
            color: #111827;
        }
        .mem-hero-metric-pill{
            margin-top: 4px;
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 10px;
            background: #eff6ff;
            color: #1d4ed8;
        }
        .mem-status-legend-wrapper{
            margin-top: 10px;
            overflow-x: auto;
            padding-bottom: 4px;
        }
        .mem-status-legend{
            display: inline-flex;
            flex-wrap: nowrap;
            gap: 8px;
            font-size: 11px;
            white-space: nowrap;
        }
        .mem-status-legend-item{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            background: #ffffff;
            border: 1px solid #e5e7eb;
        }
        .mem-status-dot{
            width: 10px;
            height: 10px;
            border-radius: 999px;
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
        /* แกนแผนสอบเทียบ (ใช้ต่อด้านล่าง) */
        .mem-cal-summary-row{
            display:flex;
            flex-wrap:wrap;
            gap:12px;
            margin-top:18px;
        }
        .mem-cal-summary-card{
            flex:1 1 0;
            min-width:160px;
            background:#FFFFFF;
            border-radius:22px;
            padding:16px 18px;
            text-align:center;
            box-shadow:0 18px 40px rgba(15,23,42,0.08);
            border:1px solid #E5E7EB;
        }
        .mem-cal-summary-value{
            font-size:26px;
            font-weight:800;
            margin-bottom:4px;
        }
        .mem-cal-summary-label{
            font-size:12px;
            color:#6B7280;
        }

        .cal-equip-container{
            margin-top:12px;
        }
        .cal-equip-card{
            background:#FFFFFF;
            border-radius:20px;
            padding:10px 14px;
            box-shadow:0 14px 30px rgba(15,23,42,0.08);
            border-left:4px solid #4F46E5;
            margin-bottom:10px;
        }
        .cal-equip-title{
            font-size:14px;
            font-weight:700;
            margin-bottom:2px;
            color:#111827;
        }
        .cal-equip-meta{
            font-size:11px;
            color:#6B7280;
        }
        .cal-equip-note{
            margin-top:4px;
            font-size:11px;
            color:#4B5563;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Excel helpers (ครุภัณฑ์)
# =========================
def get_available_excel_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sorted([p.name for p in DATA_DIR.glob("*.xls*")])


def init_excel_file_name():
    if "excel_file_name" in st.session_state:
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = get_available_excel_files()

    if files:
        st.session_state["excel_file_name"] = (
            DEFAULT_EXCEL_NAME if DEFAULT_EXCEL_NAME in files else files[0]
        )
    elif DEFAULT_EXCEL_PATH.exists():
        st.session_state["excel_file_name"] = DEFAULT_EXCEL_NAME
    else:
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

        # ---- คอลัมน์ที่ใช้กับระบบแจ้งซ่อม ----
        if MAINT_REQUEST_DATE_COL not in df.columns:
            df[MAINT_REQUEST_DATE_COL] = ""
        if MAINT_EST_DAYS_COL not in df.columns:
            df[MAINT_EST_DAYS_COL] = pd.NA
        if MAINT_DUE_DATE_COL not in df.columns:
            df[MAINT_DUE_DATE_COL] = ""
        if MAINT_EVAL_COL not in df.columns:
            df[MAINT_EVAL_COL] = MAINT_EVAL_CHOICES[0]
        if MAINT_NOTE_COL not in df.columns:
            df[MAINT_NOTE_COL] = ""

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
# Helpers แจ้งซ่อม / Timer
# =========================
def build_maintenance_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "สถานะแจ้งซ่อม" not in df.columns:
        return pd.DataFrame()
    summary = (
        df["สถานะแจ้งซ่อม"]
        .fillna(MAINT_STATUS_CHOICES[0])
        .value_counts()
        .rename_axis("สถานะแจ้งซ่อม")
        .reset_index(name="จำนวน (รายการ)")
    )
    return summary


def calculate_maintenance_timers(df: pd.DataFrame) -> pd.DataFrame:
    if "สถานะแจ้งซ่อม" not in df.columns:
        return pd.DataFrame()
    if MAINT_REQUEST_DATE_COL not in df.columns:
        return pd.DataFrame()

    req_dates = pd.to_datetime(df[MAINT_REQUEST_DATE_COL], errors="coerce")
    today = pd.to_datetime(pd.Timestamp.today().normalize())
    days_passed = (today - req_dates).dt.days

    if MAINT_EST_DAYS_COL in df.columns:
        est_days = pd.to_numeric(df[MAINT_EST_DAYS_COL], errors="coerce")
    else:
        est_days = pd.Series(pd.NA, index=df.index)

    mask_open = (
        df["สถานะแจ้งซ่อม"].isin(["แจ้งซ่อมแล้ว - กำลังดำเนินการ"])
        & req_dates.notna()
    )
    timers_df = df.loc[mask_open].copy()
    if timers_df.empty:
        return timers_df

    est_days_open = est_days[mask_open].fillna(7).astype("int64")
    req_dates_open = req_dates[mask_open]

    timers_df["row_index"] = timers_df.index
    timers_df[MAINT_REQUEST_DATE_COL] = req_dates_open.dt.date
    timers_df[MAINT_EST_DAYS_COL] = est_days_open
    timers_df["จำนวนวันที่ผ่านไป"] = days_passed[mask_open].astype("int64")
    timers_df["เหลือเวลาซ่อมตามกำหนด(วัน)"] = (
        timers_df[MAINT_EST_DAYS_COL] - timers_df["จำนวนวันที่ผ่านไป"]
    )

    due_dates = (req_dates_open + pd.to_timedelta(est_days_open, unit="D")).dt.date
    timers_df[MAINT_DUE_DATE_COL] = due_dates

    def status_label(days_left: int) -> str:
        if days_left < 0:
            return "ครบกำหนด / หมดอายุ"
        if days_left <= 2:
            return "ใกล้ครบกำหนด"
        return "อยู่ในระยะเวลา"

    timers_df["สถานะแจ้งเตือน"] = timers_df["เหลือเวลาซ่อมตามกำหนด(วัน)"].apply(
        lambda x: status_label(int(x))
    )

    cols = []
    if ASSET_CODE_COL in timers_df.columns:
        cols.append(ASSET_CODE_COL)
    if "ชื่อ" in timers_df.columns:
        cols.append("ชื่อ")
    cols += [
        "สถานะแจ้งซ่อม",
        MAINT_REQUEST_DATE_COL,
        MAINT_EST_DAYS_COL,
        MAINT_DUE_DATE_COL,
        "จำนวนวันที่ผ่านไป",
        "เหลือเวลาซ่อมตามกำหนด(วัน)",
        "สถานะแจ้งเตือน",
        "row_index",
    ]
    timers_df = timers_df[cols]
    return timers_df


def export_maintenance_excel(df: pd.DataFrame) -> BytesIO:
    summary_df = build_maintenance_summary(df)
    timers_df = calculate_maintenance_timers(df)

    if "row_index" in timers_df.columns:
        timers_export = timers_df.drop(columns=["row_index"])
    else:
        timers_export = timers_df

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        if not summary_df.empty:
            summary_df.to_excel(writer, sheet_name="สรุปสถานะแจ้งซ่อม", index=False)
        if not timers_export.empty:
            timers_export.to_excel(writer, sheet_name="รายการแจ้งซ่อม", index=False)
    buffer.seek(0)
    return buffer


def ensure_request_dates(df: pd.DataFrame):
    if MAINT_REQUEST_DATE_COL not in df.columns:
        df[MAINT_REQUEST_DATE_COL] = ""

    df_new = df.copy()
    req_dates = pd.to_datetime(df_new[MAINT_REQUEST_DATE_COL], errors="coerce")
    today = pd.to_datetime(pd.Timestamp.today().normalize())

    mask_need = (
        df_new["สถานะแจ้งซ่อม"].astype(str).eq("แจ้งซ่อมแล้ว - กำลังดำเนินการ")
        & req_dates.isna()
    )
    df_new.loc[mask_need, MAINT_REQUEST_DATE_COL] = today.date()
    return df_new, int(mask_need.sum())


# =========================
# แผนสอบเทียบ (เวอร์ชันง่าย)
# =========================
def load_calibration_plan() -> pd.DataFrame:
    if CAL_PLAN_SIMPLE_PATH.exists():
        try:
            df = pd.read_excel(CAL_PLAN_SIMPLE_PATH)
            return df.dropna(how="all").reset_index(drop=True)
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ {CAL_PLAN_SIMPLE_NAME} ได้: {e}")
            return pd.DataFrame()
    return pd.DataFrame()


def save_calibration_plan(df: pd.DataFrame):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_excel(CAL_PLAN_SIMPLE_PATH, index=False)
        st.success(f"บันทึกแผนสอบเทียบลงไฟล์: {CAL_PLAN_SIMPLE_NAME} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์แผนสอบเทียบ: {e}")


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
# Helper: Altair style
# =========================
def styled_chart(chart: alt.Chart, width: int, height: int) -> alt.Chart:
    return (
        chart.properties(width=width, height=height)
        .configure_view(stroke="#E5E7EB", strokeWidth=1, fill="#FFFFFF")
    )


# =========================
# Landing page
# =========================
def landing_page():
    set_landing_style()

    st.markdown(
        """
        <div class="landing-wrapper">
          <div class="landing-hero-icon"><span>🏥</span></div>
          <div class="landing-title">
            บริหารเครื่องมือแพทย์อย่างมืออาชีพ<br>
            เพื่อผลการตรวจที่แม่นยำและปลอดภัย
            <span class="landing-title-highlight">แบบ Real-time</span>
          </div>
          <div class="landing-subtitle">
            จัดการครุภัณฑ์เครื่องมือแพทย์ ตั้งแต่ทะเบียน ประวัติการใช้งาน การแจ้งซ่อม 
            และข้อมูลห้องปฏิบัติการ ให้ทุกคนใช้ข้อมูลชุดเดียวกัน
            รองรับการตรวจประเมินคุณภาพมาตรฐานต่าง ๆ ได้อย่างมั่นใจ
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-buttons">', unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="small")

    with col1:
        st.markdown('<div class="btn-outline">', unsafe_allow_html=True)
        start_btn = st.button("เริ่มใช้งานระบบ", key="landing_start", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
        login_btn = st.button("เข้าสู่ระบบ", key="landing_login", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="landing-note">สำหรับเจ้าหน้าที่ที่ได้รับสิทธิ์ใช้งานในห้องปฏิบัติการและหน่วยงานที่เกี่ยวข้องเท่านั้น</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="feature-row">
          <div class="feature-card">
            <div class="feature-icon">✅</div>
            <div class="feature-title">ทะเบียนครุภัณฑ์ละเอียดครบถ้วน</div>
            <div class="feature-text">
              บันทึกข้อมูลครุภัณฑ์แต่ละรายการ เช่น รุ่น หมายเลขเครื่อง Serial Number
              มูลค่า วันที่รับเข้า และตำแหน่งการใช้งานปัจจุบัน ให้ง่ายต่อการตรวจสอบย้อนหลัง
            </div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📱</div>
            <div class="feature-title">ตรวจเช็กครุภัณฑ์ด้วยสแกน QR Code</div>
            <div class="feature-text">
              ติด QR ที่อุปกรณ์เพื่อสแกนเปิดหน้าข้อมูลได้ทันทีจากมือถือ
              แสดงรูปครุภัณฑ์ ประวัติการใช้งาน และสถานะแจ้งซ่อมล่าสุดในที่เดียว
            </div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Dashboard สรุปภาพรวมแบบ Real-time</div>
            <div class="feature-text">
              เห็นจำนวนครุภัณฑ์แยกตามสถานะ ห้องที่มีครุภัณฑ์มากที่สุด
              และข้อมูลสำคัญที่ช่วยเตรียมเอกสารสำหรับการตรวจประเมินมาตรฐานต่าง ๆ
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if start_btn or login_btn:
        st.session_state.view = "login"
        st.session_state.logged_in = False
        st.experimental_rerun()


# =========================
# Login / Register page
# =========================
def login_page():
    set_login_style()

    st.markdown('<div class="mem-login-title">เข้าสู่ระบบ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mem-login-sub">Medical Equipment Management System</div>',
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["เข้าสู่ระบบ", "สมัครสมาชิกใหม่"])

    # ---------- TAB LOGIN ----------
    with tab_login:
        username = st.text_input("👤 ชื่อผู้ใช้", key="login_username")
        password = st.text_input("🔐 รหัสผ่าน", type="password", key="login_password")

        st.markdown('<div class="mem-login-btn">', unsafe_allow_html=True)
        login_clicked = st.button("เข้าสู่ระบบ", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        back_clicked = st.button("⬅️ กลับไปหน้าแรก", use_container_width=True)

        if login_clicked:
            ok, display_name, role = auth_login(username, password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.display_name = display_name
                st.session_state.current_role = role
                st.session_state.view = "app"
                st.experimental_rerun()
            else:
                st.error("ไม่พบบัญชีผู้ใช้งานนี้ในระบบ หรือรหัสผ่านไม่ถูกต้อง")

        if back_clicked:
            st.session_state.view = "landing"
            st.session_state.logged_in = False
            st.experimental_rerun()

    # ---------- TAB REGISTER ----------
    with tab_register:
        new_fullname = st.text_input("ชื่อ-สกุล", key="reg_fullname")
        new_username = st.text_input("ชื่อผู้ใช้ (ใช้ล็อกอิน)", key="reg_username")
        new_email = st.text_input("อีเมล (ถ้ามี)", key="reg_email")
        new_pwd1 = st.text_input("รหัสผ่าน", type="password", key="reg_pwd1")
        new_pwd2 = st.text_input("ยืนยันรหัสผ่าน", type="password", key="reg_pwd2")

        st.markdown('<div class="mem-login-btn">', unsafe_allow_html=True)
        reg_clicked = st.button("สมัครสมาชิก", use_container_width=True, key="btn_register")
        st.markdown("</div>", unsafe_allow_html=True)

        if reg_clicked:
            if not new_username or not new_pwd1:
                st.warning("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            elif new_pwd1 != new_pwd2:
                st.warning("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
            else:
                ok, msg = auth_register(new_username, new_pwd1, new_fullname, new_email)
                if ok:
                    st.success(msg or "สมัครสมาชิกสำเร็จ สามารถนำชื่อผู้ใช้ไปล็อกอินได้เลย")
                else:
                    st.error(msg or "สมัครสมาชิกไม่สำเร็จ กรุณาลองใหม่หรือติดต่อผู้ดูแลระบบ")

    st.markdown(
        '<div class="mem-login-footer">หากลืมรหัสผ่าน กรุณาติดต่อผู้ดูแลระบบ</div>',
        unsafe_allow_html=True,
    )


# =========================
# หน้า "หน้าหลัก"
# =========================
def page_home():
    set_main_style()

    st.markdown(
        """
        <div style="margin-bottom: 0.2rem;">
            <div class="mem-page-title">หน้าหลัก</div>
            <div class="mem-page-subtitle">
                ภาพรวมการจัดการครุภัณฑ์ และเครื่องมือห้องปฏิบัติการ (ดึงข้อมูลจากไฟล์ Excel ที่เลือกอยู่)
            </div>
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

    status_counts = (
        df[status_col]
        .fillna("ไม่ทราบสถานะ")
        .value_counts()
        .rename_axis("สถานะ")
        .reset_index(name="count")
    )

    total = int(status_counts["count"].sum())
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

    loc_col = "สถานที่ใช้งาน (ปัจจุบัน)"
    loc_total = 0
    top_loc_name = "ไม่พบข้อมูล"
    top_loc_count = 0

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

    def get_count(label: str) -> int:
        try:
            return int(status_counts.loc[status_counts["สถานะ"] == label, "count"].sum())
        except Exception:
            return 0

    cnt_total = total
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
    legend_html = "".join(
        f'<div class="mem-status-legend-item">'
        f'<span class="mem-status-dot" style="background:{c};"></span>'
        f'<span>{label}</span>'
        f'</div>'
        for label, c in legend_items
    )

    hero_html = (
        '<div class="mem-hero">'
        '<div class="mem-hero-title">จำนวนครุภัณฑ์</div>'
        '<div class="mem-hero-sub">'
        'สรุปจำนวนครุภัณฑ์ทั้งหมด แยกตามสถานะ และจำนวนตามสถานที่ใช้งานจากข้อมูลล่าสุดในระบบ'
        '</div>'
        '<div class="mem-hero-metrics">'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">รวมครุภัณฑ์ทั้งหมด</div>'
        f'<div class="mem-hero-metric-value">{cnt_total}</div>'
        '<span class="mem-hero-metric-pill">ทั้งหมด</span>'
        '</div>'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">พร้อมใช้งาน</div>'
        f'<div class="mem-hero-metric-value">{cnt_ready}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#dcfce7;color:#166534;">สถานะดี</span>'
        '</div>'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">ชำรุด (ซ่อมแซมได้)</div>'
        f'<div class="mem-hero-metric-value">{cnt_repairable}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#ffedd5;color:#9a3412;">ต้องซ่อมแซม</span>'
        '</div>'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">ชำรุด (ซ่อมแซมไม่ได้)</div>'
        f'<div class="mem-hero-metric-value">{cnt_unrepairable}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#fee2e2;color:#991b1b;">พิจารณาจัดหาใหม่</span>'
        '</div>'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">ตรวจไม่พบ / สูญหาย</div>'
        f'<div class="mem-hero-metric-value">{cnt_missing}</div>'
        '<span class="mem-hero-metric-pill" '
        'style="background:#e5e7eb;color:#111827;">ติดตามตรวจสอบ</span>'
        '</div>'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">จำนวนสถานที่ใช้งานทั้งหมด</div>'
        f'<div class="mem-hero-metric-value">{loc_total}</div>'
        '<span class="mem-hero-metric-pill">ตามไฟล์ Excel</span>'
        '</div>'
        f'<div class="mem-hero-metric">'
        '<div class="mem-hero-metric-label">สถานที่ที่มีครุภัณฑ์มากที่สุด</div>'
        f'<div class="mem-hero-metric-value" style="font-size:14px;">{top_loc_name}</div>'
        f'<span class="mem-hero-metric-pill" '
        'style="background:#cffafe;color:#0f766e;">'
        f'{top_loc_count} รายการ</span>'
        '</div>'
        '</div>'
        '<div class="mem-status-legend-wrapper"><div class="mem-status-legend">'
        f'{legend_html}'
        '</div></div>'
        '</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    base_pie = (
        alt.Chart(status_counts)
        .encode(
            theta=alt.Theta("count:Q", stack=True),
            color=alt.Color(
                "สถานะ:N",
                scale=alt_color_scale,
                legend=alt.Legend(title="สถานะ"),
            ),
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
        st.dataframe(status_table_df, hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# ตาราง + เลือกแถว (view only)
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
                if st.button("ใช้ไฟล์นี้", key="btn_use_excel"):
                    st.session_state["excel_file_name"] = selected_file
                    st.success(f"กำลังใช้งานไฟล์: {selected_file}")
                    st.experimental_rerun()
            with col_path:
                path = DATA_DIR / current_name
                st.caption(f"ไฟล์ที่ใช้งานอยู่: **{current_name}**\n\nที่อยู่ไฟล์: `{path}`")

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
                st.experimental_rerun()
            except Exception as e:
                st.error(f"ไม่สามารถบันทึกไฟล์ได้: {e}")

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลในไฟล์ Excel ที่เลือกอยู่")
        return

    st.markdown("### ตารางรายการครุภัณฑ์ (ดูอย่างเดียว)")
    equipment_table_with_selection(df)

    # เฉพาะ admin ที่เห็นปุ่มลบ
    if is_admin():
        st.markdown("#### จัดการลบข้อมูล (เฉพาะผู้ดูแลระบบ)")
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
                    st.success(f"ลบ {len(rows)} รายการเรียบร้อยแล้ว")
                    st.experimental_rerun()
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
                    st.success("ลบข้อมูลทั้งหมดจากตารางเรียบร้อยแล้ว")
                    st.experimental_rerun()
    else:
        st.info("สิทธิ์ลบข้อมูลมีเฉพาะผู้ดูแลระบบ (admin) เท่านั้น")

    # ---- เลือกครุภัณฑ์เพื่อดู/แจ้งซ่อม ----
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
        "เลือกครุภัณฑ์สำหรับดูรายละเอียด / แจ้งซ่อม",
        options=options_index,
        index=default_idx,
        format_func=format_option,
        key="equip_select_box",
    )
    st.session_state.selected_row_idx = selected_idx_box
    selected_idx = selected_idx_box

    st.markdown("### รายละเอียดครุภัณฑ์")
    if len(df) == 0:
        st.info("ยังไม่มีข้อมูลให้แสดง")
        return

    row = df.iloc[selected_idx].copy()
    asset_code = str(row.get(ASSET_CODE_COL, ""))

    # ----------------- ฟอร์มรายละเอียดครุภัณฑ์ -----------------
    st.markdown("#### ข้อมูลทั่วไปของครุภัณฑ์", unsafe_allow_html=True)

    columns_list = [
        c
        for c in df.columns
        if c
        not in (
            "รูปภาพครุภัณฑ์",
            "สถานะแจ้งซ่อม",
            MAINT_REQUEST_DATE_COL,
            MAINT_EST_DAYS_COL,
            MAINT_DUE_DATE_COL,
            MAINT_EVAL_COL,
            MAINT_NOTE_COL,
        )
    ]
    half = (len(columns_list) + 1) // 2
    left_cols = columns_list[:half]
    right_cols = columns_list[half:]

    col_left, col_right = st.columns(2)
    updated_values: dict[str, str] = {}
    can_edit_main_fields = is_admin()

    with col_left:
        for col_name in left_cols:
            current_val = row.get(col_name, "")
            new_val = st.text_input(
                str(col_name),
                value="" if pd.isna(current_val) else str(current_val),
                key=f"detail_left_{col_name}_{selected_idx}",
                disabled=not can_edit_main_fields,
            )
            updated_values[col_name] = new_val

    with col_right:
        for col_name in right_cols:
            current_val = row.get(col_name, "")
            new_val = st.text_input(
                str(col_name),
                value="" if pd.isna(current_val) else str(current_val),
                key=f"detail_right_{col_name}_{selected_idx}",
                disabled=not can_edit_main_fields,
            )
            updated_values[col_name] = new_val

    # ----------------- ส่วนแจ้งซ่อม/หมายเหตุ (ทุกคนใช้ได้) -----------------
    st.markdown("### แจ้งซ่อม / สถานะแจ้งซ่อม & หมายเหตุ", unsafe_allow_html=True)

    current_maint = str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or "")
    if current_maint not in MAINT_STATUS_CHOICES:
        current_maint = MAINT_STATUS_CHOICES[0]

    maint_select = st.selectbox(
        "สถานะแจ้งซ่อม",
        MAINT_STATUS_CHOICES,
        index=MAINT_STATUS_CHOICES.index(current_maint),
        key=f"maint_status_{selected_idx}",
    )
    updated_values["สถานะแจ้งซ่อม"] = maint_select

    current_note = str(row.get(MAINT_NOTE_COL, "") or "")
    maint_note = st.text_area(
        "เหตุผลการแจ้งซ่อม / หมายเหตุ (ผู้ใช้ทั่วไปแก้ได้)",
        value=current_note,
        key=f"maint_note_{selected_idx}",
    )
    updated_values[MAINT_NOTE_COL] = maint_note

    # ----------------- QR & รูปภาพ -----------------
    st.markdown("### QR Code และรูปภาพครุภัณฑ์")
    qr_col, img_col = st.columns([1, 1])

    with qr_col:
        st.subheader("QR Code ของครุภัณฑ์")
        url_for_qr = f"https://mem-system-dashboard.streamlit.app/?code={asset_code}"
        qr_bytes_for_download = generate_qr_bytes_for_url(url_for_qr)
        st.image(qr_bytes_for_download, use_column_width=True)
        st.caption(asset_code)
        st.write("สแกน QR นี้เพื่อเปิดหน้าข้อมูลครุภัณฑ์จากอุปกรณ์อื่น ๆ ได้เช่นกัน")

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
            "อัปโหลดรูปภาพใหม่ (เฉพาะผู้ดูแลระบบ)",
            type=["png", "jpg", "jpeg"],
            key=f"upload_image_{selected_idx}",
            disabled=not is_admin(),
        )

    # ----------------- ปุ่มบันทึก -----------------
    st.write("")
    if st.button("บันทึกข้อมูลครุภัณฑ์ / แจ้งซ่อม", type="primary"):
        df_current = load_equipment_data()
        if selected_idx >= len(df_current):
            st.error("แถวข้อมูลนี้ไม่อยู่ในตารางแล้ว กรุณารีเฟรชหน้าเว็บ")
            return

        # อัปเดตข้อมูลหลัก เฉพาะ admin
        if is_admin():
            for col in updated_values:
                if col not in df_current.columns:
                    continue
                if col in ("สถานะแจ้งซ่อม", MAINT_NOTE_COL):
                    # ไปจัดการทีหลัง
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

        # อัปเดตสถานะแจ้งซ่อม + หมายเหตุ (ทุกคน)
        df_current.at[selected_idx, "สถานะแจ้งซ่อม"] = updated_values["สถานะแจ้งซ่อม"]
        df_current.at[selected_idx, MAINT_NOTE_COL] = updated_values[MAINT_NOTE_COL]

        # ถ้าสถานะแจ้งซ่อม = แจ้งซ่อมแล้ว และยังไม่มีวันที่ → ใส่วันที่วันนี้
        if updated_values["สถานะแจ้งซ่อม"] == "แจ้งซ่อมแล้ว - กำลังดำเนินการ":
            old_date = df_current.at[selected_idx, MAINT_REQUEST_DATE_COL]
            if not old_date:
                df_current.at[selected_idx, MAINT_REQUEST_DATE_COL] = datetime.today().date()

        # อัปเดตรูปภาพ ถ้ามี (เฉพาะ admin)
        if uploaded_img is not None and is_admin():
            filename = save_uploaded_image(uploaded_img, asset_code)
            if "รูปภาพครุภัณฑ์" not in df_current.columns:
                df_current["รูปภาพครุภัณฑ์"] = ""
            df_current.at[selected_idx, "รูปภาพครุภัณฑ์"] = filename

        save_equipment_data(df_current)
        st.success("บันทึกข้อมูลเรียบร้อยแล้ว")
        st.experimental_rerun()


# =========================
# หน้า "แจ้งซ่อม / บำรุงรักษา"
# =========================
def page_maintenance():
    set_main_style()
    st.markdown(
        '<div class="mem-page-title">แจ้งซ่อม / บำรุงรักษา</div>',
        unsafe_allow_html=True,
    )

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel ที่เลือกอยู่")
        return

    for col in [
        MAINT_REQUEST_DATE_COL,
        MAINT_EST_DAYS_COL,
        MAINT_DUE_DATE_COL,
        MAINT_EVAL_COL,
        MAINT_NOTE_COL,
    ]:
        if col not in df.columns:
            if col == MAINT_EST_DAYS_COL:
                df[col] = pd.NA
            elif col == MAINT_EVAL_COL:
                df[col] = MAINT_EVAL_CHOICES[0]
            else:
                df[col] = ""

    df_filled, added_dates = ensure_request_dates(df)
    if added_dates > 0:
        save_equipment_data(df_filled)
        df = df_filled
        st.info(
            f"ระบบได้เติมวันที่แจ้งซ่อม (วันนี้) ให้ {added_dates} รายการที่ยังไม่มีวันที่แจ้งซ่อมแล้ว"
        )

    if "สถานะแจ้งซ่อม" not in df.columns:
        st.warning("ไม่พบคอลัมน์ 'สถานะแจ้งซ่อม' ในไฟล์ Excel")
        return

    maint_counts = build_maintenance_summary(df)

    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">ภาพรวมสถานะแจ้งซ่อม</div>
            <div class="mem-card-subtitle">
                แสดงจำนวนครุภัณฑ์ตามสถานะแจ้งซ่อม ดึงข้อมูลจากไฟล์ Excel เดียวกับหน้า QR
                เมื่อมีการแจ้งซ่อมหรือเปลี่ยนสถานะจากหน้า QR/รายละเอียดครุภัณฑ์ ข้อมูลในหน้านี้จะอัปเดตอัตโนมัติ
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        chart = (
            alt.Chart(maint_counts)
            .mark_bar()
            .encode(
                x=alt.X("สถานะแจ้งซ่อม:N", sort=None, title="สถานะแจ้งซ่อม"),
                y=alt.Y("จำนวน (รายการ):Q", title="จำนวน (รายการ)"),
                tooltip=["สถานะแจ้งซ่อม:N", "จำนวน (รายการ):Q"],
            )
        )
        chart = styled_chart(chart, width=500, height=320)
        st.altair_chart(chart, use_container_width=True)
    with col_table:
        st.dataframe(maint_counts, hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">รายการแจ้งซ่อมและเวลาคงเหลือ</div>
            <div class="mem-card-subtitle">
                ใช้ 'วันที่แจ้งซ่อมล่าสุด' และ 'ระยะเวลาซ่อมที่กำหนด (วัน)' 
                เพื่อคำนวณจำนวนวันที่ผ่านไปและเวลาเหลือ
            </div>
        """,
        unsafe_allow_html=True,
    )

    timers_df = calculate_maintenance_timers(df)
    if timers_df.empty:
        st.info(
            "ยังไม่มีรายการแจ้งซ่อมที่อยู่ในสถานะ 'แจ้งซ่อมแล้ว - กำลังดำเนินการ' พร้อมข้อมูลวันที่แจ้งซ่อม"
        )
    else:
        display_cols = [c for c in timers_df.columns if c != "row_index"]
        st.dataframe(
            timers_df[display_cols],
            hide_index=True,
            use_container_width=True,
        )

        excel_bytes = export_maintenance_excel(df)
        st.download_button(
            "⬇️ ดาวน์โหลดข้อมูลแจ้งซ่อม (Excel)",
            data=excel_bytes,
            file_name="maintenance_report.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown("#### ✅ ยืนยันการรับแจ้งซ่อม / บันทึกผลการซ่อม (เฉพาะ admin)")

        if not is_admin():
            st.info("เฉพาะผู้ดูแลระบบ (admin) ที่สามารถบันทึกผลการซ่อมจากส่วนนี้ได้")
        else:
            options = timers_df["row_index"].tolist()

            def format_req(idx: int) -> str:
                row = df.loc[idx]
                code = str(row.get(ASSET_CODE_COL, ""))
                name = str(row.get("ชื่อ", "ไม่ทราบชื่อ"))
                return f"{code} - {name}"

            selected_idx = st.selectbox(
                "เลือกรายการแจ้งซ่อม",
                options=options,
                format_func=format_req,
                key="maint_confirm_select",
            )
            row_sel = df.loc[selected_idx]

            st.write(f"**รหัสครุภัณฑ์:** {row_sel.get(ASSET_CODE_COL, '-')}")
            st.write(f"**ชื่อครุภัณฑ์:** {row_sel.get('ชื่อ', '-')}")
            st.write(f"**วันที่แจ้งซ่อมล่าสุด:** {row_sel.get(MAINT_REQUEST_DATE_COL, '-')}")

            raw_est = row_sel.get(MAINT_EST_DAYS_COL, "")
            try:
                default_est = int(raw_est)
                if default_est <= 0:
                    default_est = 7
            except Exception:
                default_est = 7

            est_days_input = st.number_input(
                "ระยะเวลาซ่อมที่กำหนด (วัน)",
                min_value=1,
                max_value=365,
                value=default_est,
                step=1,
                key=f"maint_est_days_{selected_idx}",
            )

            current_eval = str(row_sel.get(MAINT_EVAL_COL, "") or MAINT_EVAL_CHOICES[0])
            if current_eval not in MAINT_EVAL_CHOICES:
                current_eval = MAINT_EVAL_CHOICES[0]

            eval_select = st.selectbox(
                "ผลการประเมินการซ่อม",
                MAINT_EVAL_CHOICES,
                index=MAINT_EVAL_CHOICES.index(current_eval),
                key=f"maint_eval_select_{selected_idx}",
            )

            note_default = str(row_sel.get(MAINT_NOTE_COL, "") or "")
            note = st.text_area(
                "หมายเหตุเพิ่มเติม (จะบันทึกทับจากที่หน้า 'รายละเอียดครุภัณฑ์')",
                value=note_default,
                key=f"maint_note_admin_{selected_idx}",
            )

            if st.button("💾 ยืนยันการรับแจ้งซ่อม / บันทึกข้อมูล", use_container_width=True):
                df_current = load_equipment_data()
                if selected_idx not in df_current.index:
                    st.error("ไม่พบแถวข้อมูลนี้ในไฟล์แล้ว กรุณารีเฟรชหน้า")
                else:
                    req_dt = pd.to_datetime(
                        df_current.at[selected_idx, MAINT_REQUEST_DATE_COL],
                        errors="coerce",
                    )
                    if pd.isna(req_dt):
                        req_dt = pd.to_datetime(pd.Timestamp.today().normalize())
                        df_current.at[selected_idx, MAINT_REQUEST_DATE_COL] = req_dt.date()

                    df_current.at[selected_idx, MAINT_EST_DAYS_COL] = int(est_days_input)
                    df_current.at[selected_idx, MAINT_DUE_DATE_COL] = (
                        req_dt + pd.to_timedelta(int(est_days_input), unit="D")
                    ).date()
                    df_current.at[selected_idx, MAINT_EVAL_COL] = eval_select
                    df_current.at[selected_idx, MAINT_NOTE_COL] = note

                    if eval_select.startswith("ซ่อมไม่ได้"):
                        df_current.at[selected_idx, "สถานะแจ้งซ่อม"] = "ปลดระวาง / รอจำหน่าย"
                    elif eval_select.startswith("ซ่อมได้"):
                        df_current.at[selected_idx, "สถานะแจ้งซ่อม"] = "ซ่อมเสร็จแล้ว"

                    save_equipment_data(df_current)
                    st.success("บันทึกข้อมูลแจ้งซ่อมเรียบร้อยแล้ว")
                    st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# หน้า "แผนสอบเทียบ" (เวอร์ชันง่าย)
# =========================
def page_calibration():
    set_main_style()
    st.markdown(
        """
        <div style="margin-bottom: 0.2rem;">
            <div class="mem-page-title">การบำรุงรักษาและการควบคุมคุณภาพ</div>
            <div class="mem-page-subtitle">
                แผนการสอบเทียบและบำรุงรักษาเครื่องมือแพทย์ จากไฟล์ calibration_plan_simple.xlsx
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📁 อัปโหลด / แทนที่ไฟล์แผนสอบเทียบ (.xlsx)", expanded=False):
        uploaded = st.file_uploader(
            "เลือกไฟล์ Excel ของแผนสอบเทียบ (ต้องมีคอลัมน์อย่างน้อย: 'ชื่อเครื่องมือ', 'ID', 'S/N', 'DueDate', 'หมายเหตุ')",
            type=["xlsx", "xls"],
            key="cal_plan_upload",
        )
        if uploaded is not None:
            save_path = CAL_PLAN_SIMPLE_PATH
            try:
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"บันทึกไฟล์แผนสอบเทียบใหม่: {save_path.name}")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"ไม่สามารถบันทึกไฟล์แผนสอบเทียบได้: {e}")

        if CAL_PLAN_SIMPLE_PATH.exists():
            st.caption(f"ไฟล์ที่ใช้งานอยู่: **{CAL_PLAN_SIMPLE_PATH.name}**")
        else:
            st.caption("ยังไม่มีไฟล์แผนสอบเทียบในโฟลเดอร์ data")

    df = load_calibration_plan()
    if df.empty:
        st.info(
            "ยังไม่มีข้อมูลแผนสอบเทียบ ให้สร้างไฟล์ calibration_plan_simple.xlsx "
            "ด้วยคอลัมน์ เช่น: 'ชื่อเครื่องมือ', 'ID', 'S/N', 'DueDate', 'หมายเหตุ' แล้วอัปโหลดจากด้านบน"
        )
        return

    # คอลัมน์พื้นฐาน
    equip_col = "ชื่อเครื่องมือ" if "ชื่อเครื่องมือ" in df.columns else df.columns[0]
    id_col = "ID" if "ID" in df.columns else df.columns[1]
    sn_col = "S/N" if "S/N" in df.columns else df.columns[2]
    due_col = "DueDate" if "DueDate" in df.columns else df.columns[3]
    note_col = "หมายเหตุ" if "หมายเหตุ" in df.columns else None

    df[due_col] = pd.to_datetime(df[due_col], errors="coerce")
    today = pd.to_datetime(pd.Timestamp.today().normalize())
    df["days_left"] = (df[due_col] - today).dt.days

    def label_status(days):
        if pd.isna(days):
            return "ไม่มีข้อมูล"
        days_int = int(days)
        if days_int < 0:
            return "เลยกำหนดสอบเทียบ"
        if days_int <= 30:
            return "ใกล้ถึงกำหนดสอบเทียบ"
        if days_int <= 90:
            return "กำหนดในอีก 31–90 วัน"
        return "พร้อมใช้งาน"

    df["สถานะกำหนด"] = df["days_left"].apply(label_status)

    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">สรุปสถิติการสอบเทียบและบำรุงรักษา</div>
            <div class="mem-card-subtitle">
                ใช้ DueDate แบ่งกลุ่มรายการที่เลยกำหนด ใกล้ครบกำหนด และยังพร้อมใช้งาน
            </div>
        """,
        unsafe_allow_html=True,
    )

    overdue_cnt = int((df["สถานะกำหนด"] == "เลยกำหนดสอบเทียบ").sum())
    near_cal_cnt = int((df["สถานะกำหนด"] == "ใกล้ถึงกำหนดสอบเทียบ").sum())
    near_pm_cnt = int((df["สถานะกำหนด"] == "กำหนดในอีก 31–90 วัน").sum())
    ready_cnt = int((df["สถานะกำหนด"] == "พร้อมใช้งาน").sum())

    summary_html = f"""
    <div class="mem-cal-summary-row">
      <div class="mem-cal-summary-card">
        <div class="mem-cal-summary-value" style="color:#EF4444;">{overdue_cnt}</div>
        <div class="mem-cal-summary-label">เลยกำหนดสอบเทียบ</div>
      </div>
      <div class="mem-cal-summary-card">
        <div class="mem-cal-summary-value" style="color:#F97316;">{near_cal_cnt}</div>
        <div class="mem-cal-summary-label">ใกล้ถึงกำหนดสอบเทียบ (ภายใน 30 วัน)</div>
      </div>
      <div class="mem-cal-summary-card">
        <div class="mem-cal-summary-value" style="color:#A855F7;">{near_pm_cnt}</div>
        <div class="mem-cal-summary-label">กำหนดในอีก 31–90 วัน</div>
      </div>
      <div class="mem-cal-summary-card">
        <div class="mem-cal-summary-value" style="color:#22C55E;">{ready_cnt}</div>
        <div class="mem-cal-summary-label">พร้อมใช้งาน (เกิน 90 วันขึ้นไป)</div>
      </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # การ์ดรายการเครื่องมือ
    st.markdown(
        """
        <div class="mem-card">
          <div class="cal-equip-container">
            <div class="mem-card-title">รายการเครื่องมือในแผนสอบเทียบ</div>
            <div class="mem-card-subtitle">
              แสดงชื่อเครื่องมือ ID S/N DueDate และหมายเหตุ จากไฟล์แผนสอบเทียบที่ใช้งานอยู่
            </div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    cols_cards = st.columns(2)
    for i, (_, r) in enumerate(df.iterrows()):
        name = str(r.get(equip_col, "-"))
        _id = str(r.get(id_col, "-"))
        sn = str(r.get(sn_col, "-"))
        note = str(r.get(note_col, "-")) if note_col else "-"
        d = r.get(due_col)
        if pd.isna(d):
            due_str = "ไม่ระบุ"
        else:
            try:
                due_str = pd.to_datetime(d).strftime("%d/%m/%Y")
            except Exception:
                due_str = "ไม่ระบุ"

        card_html = f"""
        <div class="cal-equip-card">
          <div class="cal-equip-title">{name}</div>
          <div class="cal-equip-meta"><span>ID: {_id}</span> | <span>S/N: {sn}</span></div>
          <div class="cal-equip-meta">กำหนดสอบเทียบ: {due_str}</div>
          <div class="cal-equip-note">หมายเหตุ: {note}</div>
        </div>
        """
        with cols_cards[i % 2]:
            st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### ตารางแผนสอบเทียบ (แก้ไขได้)")
    editable_cols = [c for c in df.columns]
    edited_df = st.data_editor(
        df[editable_cols],
        key="cal_plan_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )
    if st.button("💾 บันทึกแผนสอบเทียบทั้งหมด", use_container_width=True):
        save_calibration_plan(edited_df)
        st.experimental_rerun()


# =========================
# หน้า "รายงานสรุป"
# =========================
def page_summary():
    set_main_style()
    st.markdown(
        '<div class="mem-page-title">รายงานสรุป</div>',
        unsafe_allow_html=True,
    )
    st.info("ส่วนนี้ใช้ทำรายงานสรุปครุภัณฑ์ / วิเคราะห์ข้อมูลเพิ่มเติมในอนาคต")


# =========================
# Main app (หลัง login)
# =========================
def main_app():
    set_main_style()

    with st.sidebar:
        role_label = "ผู้ดูแลระบบ" if is_admin() else "ผู้ใช้งานทั่วไป"
        st.markdown(
            f"""
            <div class="mem-sidebar-user">
              <div style="font-size:28px; font-weight:700; margin-bottom:4px;">AD</div>
              <div class="mem-sidebar-user-name">{st.session_state.get('display_name', 'ผู้ใช้งาน')}</div>
              <div class="mem-sidebar-user-sub">{role_label}</div>
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
            st.experimental_rerun()
        if menu_button("รายการครุภัณฑ์"):
            st.session_state.current_menu = "รายการครุภัณฑ์"
            st.experimental_rerun()
        if menu_button("แจ้งซ่อม / บำรุงรักษา"):
            st.session_state.current_menu = "แจ้งซ่อม / บำรุงรักษา"
            st.experimental_rerun()
        if menu_button("แผนสอบเทียบ"):
            st.session_state.current_menu = "แผนสอบเทียบ"
            st.experimental_rerun()
        if menu_button("รายงานสรุป"):
            st.session_state.current_menu = "รายงานสรุป"
            st.experimental_rerun()

        st.write("")
        if st.button("Logout", type="primary", use_container_width=True):
            # เคลียร์ session_state เฉพาะที่เกี่ยวกับ login
            for k in ["logged_in", "username", "display_name", "current_role", "current_menu"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state.view = "landing"
            st.experimental_rerun()

    menu = st.session_state.get("current_menu", "หน้าหลัก")
    if menu == "หน้าหลัก":
        page_home()
    elif menu == "รายการครุภัณฑ์":
        page_equipment_list()
    elif menu == "แจ้งซ่อม / บำรุงรักษา":
        page_maintenance()
    elif menu == "แผนสอบเทียบ":
        page_calibration()
    elif menu == "รายงานสรุป":
        page_summary()


# =========================
# ENTRY POINT
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
    main_app()
else:
    if st.session_state.view == "login":
        login_page()
    else:
        landing_page()
