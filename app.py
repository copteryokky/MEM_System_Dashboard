import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from io import BytesIO
import qrcode
import calendar as pycal   # 👈 เพิ่มใช้สร้างปฏิทิน

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH
from auth import authenticate_user

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
MAINT_NOTE_COL = "หมายเหตุการซ่อม"

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

        /* ==== Calibration page styles ==== */
        .mem-cal-column{
            background:#FFFFFF;
            border-radius:24px;
            padding:18px 20px;
            box-shadow:0 18px 40px rgba(15,23,42,0.08);
            border:1px solid #E5E7EB;
            min-height:260px;
        }
        .mem-cal-column-title{
            font-size:18px;
            font-weight:700;
            margin-bottom:8px;
            color:#111827;
        }
        .mem-cal-column-sub{
            font-size:12px;
            color:#6B7280;
            margin-bottom:12px;
        }

        /* ปฏิทินในกล่องด้านบน */
        .mem-cal-calendar{
            margin-bottom:12px;
        }
        .mem-cal-grid{
            width:100%;
            border-collapse:collapse;
            table-layout:fixed;
        }
        .mem-cal-grid th{
            font-size:11px;
            font-weight:600;
            color:#6B7280;
            padding:2px 0 6px 0;
            text-align:center;
        }
        .mem-cal-grid td{
            padding:3px 0;
            text-align:center;
        }
        .mem-cal-day{
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:26px;
            height:26px;
            border-radius:999px;
            font-size:11px;
            color:#4B5563;
        }
        .mem-cal-day-event{
            background:linear-gradient(135deg,#4F46E5,#6366F1);
            color:#FFFFFF;
            box-shadow:0 0 0 1px rgba(129,140,248,0.6);
        }

        .mem-cal-item{
            border-radius:18px;
            padding:10px 12px;
            margin-bottom:8px;
            border-left:4px solid #4F46E5;
            background:#F9FAFB;
        }
        .mem-cal-item-title{
            font-size:14px;
            font-weight:600;
        }
        .mem-cal-item-meta{
            font-size:11px;
            color:#6B7280;
        }
        .mem-cal-item-duedate{
            font-size:12px;
            margin-top:4px;
        }
        .mem-cal-empty{
            font-size:12px;
            color:#9CA3AF;
            padding-top:4px;
        }
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
# Helpers สำหรับ "แจ้งซ่อม / บำรุงรักษา"
# =========================
def build_maintenance_summary(df: pd.DataFrame) -> pd.DataFrame:
    """สรุปจำนวนครุภัณฑ์ตามสถานะแจ้งซ่อม"""
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
    """
    ตารางแจ้งเตือนเวลาคงเหลือในการซ่อม
    ใช้ 'วันที่แจ้งซ่อมล่าสุด' + 'ระยะเวลาซ่อมที่กำหนด (วัน)'
    ถ้าไม่ได้กำหนดวัน → ใช้ค่า default 7 วัน
    """
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

    # เลือกเฉพาะรายการที่แจ้งซ่อมแล้วและมีวันที่
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
    timers_df["วันที่แจ้งซ่อมล่าสุด"] = req_dates_open.dt.date
    timers_df["ระยะเวลาซ่อมที่กำหนด (วัน)"] = est_days_open
    timers_df["จำนวนวันที่ผ่านไป"] = days_passed[mask_open].astype("int64")
    timers_df["เหลือเวลาซ่อมตามกำหนด(วัน)"] = (
        timers_df["ระยะเวลาซ่อมที่กำหนด (วัน)"] - timers_df["จำนวนวันที่ผ่านไป"]
    )

    due_dates = (req_dates_open + pd.to_timedelta(est_days_open, unit="D")).dt.date
    timers_df["กำหนดซ่อมเสร็จภายใน"] = due_dates

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
        "วันที่แจ้งซ่อมล่าสุด",
        "ระยะเวลาซ่อมที่กำหนด (วัน)",
        "กำหนดซ่อมเสร็จภายใน",
        "จำนวนวันที่ผ่านไป",
        "เหลือเวลาซ่อมตามกำหนด(วัน)",
        "สถานะแจ้งเตือน",
        "row_index",
    ]
    timers_df = timers_df[cols]
    return timers_df


def expire_old_maintenance(df: pd.DataFrame, default_limit: int = 7):
    """
    เคลียร์สถานะแจ้งซ่อมของรายการที่เกิน 'ระยะเวลาซ่อมที่กำหนด (วัน)'
    ถ้าไม่ได้กำหนดวัน → ใช้ default_limit (7 วัน)
    เฉพาะรายการที่ยังเป็น 'แจ้งซ่อมแล้ว - กำลังดำเนินการ'
    """
    if "สถานะแจ้งซ่อม" not in df.columns:
        return df, 0
    if MAINT_REQUEST_DATE_COL not in df.columns:
        return df, 0

    df_new = df.copy()
    req_dates = pd.to_datetime(df_new[MAINT_REQUEST_DATE_COL], errors="coerce")
    today = pd.to_datetime(pd.Timestamp.today().normalize())
    days_diff = (today - req_dates).dt.days

    # ใช้ระยะเวลาซ่อมรายรายการ ถ้าไม่มีให้ใช้ default_limit
    if MAINT_EST_DAYS_COL in df_new.columns:
        limits = pd.to_numeric(df_new[MAINT_EST_DAYS_COL], errors="coerce")
        limits = limits.fillna(default_limit).astype("int64")
    else:
        limits = pd.Series(default_limit, index=df_new.index, dtype="int64")

    mask_expire = (
        df_new["สถานะแจ้งซ่อม"].isin(["แจ้งซ่อมแล้ว - กำลังดำเนินการ"])
        & req_dates.notna()
        & (days_diff > limits)
    )

    expired_count = int(mask_expire.sum())
    if expired_count == 0:
        return df_new, 0

    # รีเซ็ตสถานะ + ล้างข้อมูลแจ้งซ่อม → ต้องแจ้งใหม่
    df_new.loc[mask_expire, "สถานะแจ้งซ่อม"] = MAINT_STATUS_CHOICES[0]
    df_new.loc[mask_expire, MAINT_REQUEST_DATE_COL] = ""
    if MAINT_EST_DAYS_COL in df_new.columns:
        df_new.loc[mask_expire, MAINT_EST_DAYS_COL] = pd.NA
    if MAINT_DUE_DATE_COL in df_new.columns:
        df_new.loc[mask_expire, MAINT_DUE_DATE_COL] = ""
    if MAINT_EVAL_COL in df_new.columns:
        df_new.loc[mask_expire, MAINT_EVAL_COL] = MAINT_EVAL_CHOICES[0]
    if MAINT_NOTE_COL in df_new.columns:
        df_new.loc[mask_expire, MAINT_NOTE_COL] = ""

    return df_new, expired_count


def export_maintenance_excel(df: pd.DataFrame) -> BytesIO:
    """
    สร้างไฟล์ Excel สำหรับข้อมูลแจ้งซ่อม
    - Sheet1: สรุปสถานะแจ้งซ่อม
    - Sheet2: รายการแจ้งซ่อม + เวลาคงเหลือ
    """
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
    """
    เติมวันที่แจ้งซ่อมให้รายการที่สถานะแจ้งซ่อม = 'แจ้งซ่อมแล้ว - กำลังดำเนินการ'
    แต่ช่องวันที่ยังว่างอยู่ → ใช้วันที่วันนี้เป็นวันที่แจ้งซ่อม
    """
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
# Helpers สำหรับ "แผนสอบเทียบ"
# =========================
def parse_calibration_from_file(path: Path) -> pd.DataFrame:
    """อ่านไฟล์แผนสอบเทียบแบบเดิม (มีหัวตารางหลายแถว) แล้วจัดให้อยู่ในรูปตาราง DataFrame เดียว"""
    try:
        xls = pd.ExcelFile(path)
    except Exception:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []
    for sheet_name in xls.sheet_names:
        try:
            raw = pd.read_excel(path, sheet_name=sheet_name)
        except Exception:
            continue
        if raw.empty or len(raw) < 4:
            continue

        # ใช้แถวที่ 3 (index=2) เป็น header
        header_row = raw.iloc[2]
        df = raw.iloc[3:].copy()
        df.columns = header_row

        if "No." not in df.columns:
            continue

        df = df[pd.to_numeric(df["No."], errors="coerce").notna()].copy()
        df["แหล่งข้อมูล"] = sheet_name
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True)
    df_all = df_all.dropna(how="all").reset_index(drop=True)
    return df_all


def load_calibration_plan() -> pd.DataFrame:
    """
    โหลดข้อมูลแผนสอบเทียบ
    1) ถ้ามีไฟล์ calibration_plan_simple.xlsx → ใช้ไฟล์นี้
    2) ถ้ามีไฟล์ แผนสอบเทียบและบำรุงรักษาเครื่องมือ.xlsx → แปลงรูปแบบแล้วใช้
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if CAL_PLAN_SIMPLE_PATH.exists():
        try:
            df = pd.read_excel(CAL_PLAN_SIMPLE_PATH)
            return df.dropna(how="all").reset_index(drop=True)
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ {CAL_PLAN_SIMPLE_NAME} ได้: {e}")
            return pd.DataFrame()

    original_path = DATA_DIR / CAL_ORIGINAL_NAME
    if original_path.exists():
        df = parse_calibration_from_file(original_path)
        if not df.empty:
            return df

    return pd.DataFrame()


def save_calibration_plan(df: pd.DataFrame):
    """บันทึกแผนสอบเทียบลงไฟล์ calibration_plan_simple.xlsx"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base_cols = [c for c in df.columns if c not in ("days_left", "สถานะกำหนด")]

    df_to_save = df[base_cols].copy()
    try:
        df_to_save.to_excel(CAL_PLAN_SIMPLE_PATH, index=False)
        st.success(f"บันทึกแผนสอบเทียบลงไฟล์: {CAL_PLAN_SIMPLE_NAME} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์แผนสอบเทียบ: {e}")


def import_calibration_from_uploaded(uploaded_file) -> pd.DataFrame:
    """รับไฟล์ที่อัปโหลด → พยายามแปลงแบบเดิมก่อน ถ้าไม่ได้ให้ลองอ่านตรง ๆ"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = DATA_DIR / "_uploaded_cal_plan_temp.xlsx"

    try:
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = parse_calibration_from_file(temp_path)
        if df.empty:
            try:
                df = pd.read_excel(temp_path)
            except Exception:
                df = pd.DataFrame()
        return df.dropna(how="all").reset_index(drop=True)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

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


def get_qr_image_path_from_row(row: pd.Series) -> Path | None:
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

    # ปุ่ม
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

    # การ์ด 3 ใบ
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
        st.rerun()

# =========================
# Login page
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
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.display_name = display_name
            st.session_state.view = "app"
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")

# =========================
# Helper: Altair style
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
    legend_html_parts = []
    for label, color in legend_items:
        legend_html_parts.append(
            f'<div class="mem-status-legend-item">'
            f'<span class="mem-status-dot" style="background:{color};"></span>'
            f'<span>{label}</span>'
            f'</div>'
        )
    legend_html = "".join(legend_html_parts)

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

    labels = (
        base_pie.mark_text(radius=110, size=13, color="#111827", fontWeight="bold")
        .encode(text="label_short:N")
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

# =========================
# ตาราง + เลือกแถว
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
                    st.rerun()
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
                st.rerun()
            except Exception as e:
                st.error(f"ไม่สามารถบันทึกไฟล์ได้: {e}")

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลในไฟล์ Excel ที่เลือกอยู่")
        return

    st.markdown("### ตารางรายการครุภัณฑ์")
    equipment_table_with_selection(df)

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
                st.success(f"ลบ {len(rows)} รายการเรียบร้อยแล้ว")
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
                st.success("ลบข้อมูลทั้งหมดจากตารางเรียบร้อยแล้ว")
                st.rerun()

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

    columns_list = [
        c
        for c in df.columns
        if c not in (
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
            url_for_qr = f"https://memsystemdashboard-qr.streamlit.app/?code={asset_code}"
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

    # ให้แน่ใจว่ามีคอลัมน์ที่ใช้กับแจ้งซ่อมครบ
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

    # เติมวันที่แจ้งซ่อมให้รายการที่สถานะ = "แจ้งซ่อมแล้ว - กำลังดำเนินการ" แต่ยังไม่มีวันที่
    df_filled, added_dates = ensure_request_dates(df)
    if added_dates > 0:
        save_equipment_data(df_filled)
        df = df_filled
        st.info(
            f"ระบบได้เติมวันที่แจ้งซ่อม (วันนี้) ให้ {added_dates} รายการที่ยังไม่มีวันที่แจ้งซ่อมแล้ว"
        )

    # เคลียร์รายการที่เกินกำหนด (ตามระยะเวลาซ่อมที่กำหนด, ถ้าไม่มีใช้ 7)
    df_after_expire, expired_count = expire_old_maintenance(df)
    if expired_count > 0:
        save_equipment_data(df_after_expire)
        df = df_after_expire
        st.warning(
            f"ระบบได้เคลียร์รายการแจ้งซ่อมที่เกินระยะเวลาซ่อมที่กำหนดแล้วจำนวน {expired_count} รายการ "
            "ผู้ใช้จำเป็นต้องแจ้งซ่อมใหม่อีกครั้ง"
        )

    if "สถานะแจ้งซ่อม" not in df.columns:
        st.warning("ไม่พบคอลัมน์ 'สถานะแจ้งซ่อม' ในไฟล์ Excel")
        return

    # ---------- การ์ดที่ 1: ภาพรวมสถานะแจ้งซ่อม ----------
    maint_counts = build_maintenance_summary(df)

    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">ภาพรวมสถานะแจ้งซ่อม</div>
            <div class="mem-card-subtitle">
                แสดงจำนวนครุภัณฑ์ตามสถานะแจ้งซ่อม ดึงข้อมูลจากไฟล์ Excel เดียวกับหน้า QR
                เมื่อมีการแจ้งซ่อมหรือเปลี่ยนสถานะจากหน้า QR ข้อมูลในหน้านี้จะอัปเดตอัตโนมัติ
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
        st.dataframe(
            maint_counts,
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- การ์ดที่ 2: รายการแจ้งซ่อม + เวลาคงเหลือ ----------
    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">รายการแจ้งซ่อมและเวลาคงเหลือ</div>
            <div class="mem-card-subtitle">
                ใช้ 'วันที่แจ้งซ่อมล่าสุด' และ 'ระยะเวลาซ่อมที่กำหนด (วัน)' 
                เพื่อคำนวณจำนวนวันที่ผ่านไปและเวลาเหลือ หากเกินกำหนดและยังอยู่ในสถานะ 
                'แจ้งซ่อมแล้ว - กำลังดำเนินการ' ระบบจะถือว่าแจ้งซ่อมหมดอายุและตั้งสถานะกลับเป็น 
                'ยังไม่เคยแจ้งซ่อม' เพื่อให้แจ้งใหม่อีกครั้ง
            </div>
        """,
        unsafe_allow_html=True,
    )

    timers_df = calculate_maintenance_timers(df)

    if timers_df.empty:
        st.info("ยังไม่มีรายการแจ้งซ่อมที่อยู่ในสถานะ 'แจ้งซ่อมแล้ว - กำลังดำเนินการ' พร้อมข้อมูลวันที่แจ้งซ่อม")
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
        st.markdown("#### ✅ ยืนยันการรับแจ้งซ่อม / ประเมินผลการซ่อม")

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
            "หมายเหตุเพิ่มเติม (ถ้ามี)",
            value=note_default,
            key=f"maint_note_{selected_idx}",
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

                # ถ้าประเมินว่า "ซ่อมไม่ได้" → เปลี่ยนสถานะเป็นปลดระวาง / รอจำหน่าย
                if eval_select.startswith("ซ่อมไม่ได้"):
                    df_current.at[selected_idx, "สถานะแจ้งซ่อม"] = "ปลดระวาง / รอจำหน่าย"

                save_equipment_data(df_current)
                st.success("บันทึกข้อมูลแจ้งซ่อมเรียบร้อยแล้ว")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# หน้า "แผนสอบเทียบ" (ปฏิทินเดือนนี้ + เดือนหน้า)
# =========================
def page_calibration():
    set_main_style()
    st.markdown(
        """
        <div style="margin-bottom: 0.2rem;">
            <div class="mem-page-title">การบำรุงรักษาและการควบคุมคุณภาพ</div>
            <div class="mem-page-subtitle">
                แผนการสอบเทียบและบำรุงรักษาเครื่องมือแพทย์ ดึงจากไฟล์ Excel แผนสอบเทียบและบำรุงรักษาเครื่องมือ
                และสามารถแก้ไข/เพิ่มข้อมูลได้จากหน้านี้
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ----------------- อัปโหลดไฟล์แผนสอบเทียบ -----------------
    with st.expander("📁 อัปโหลด / แทนที่ไฟล์แผนสอบเทียบ (.xlsx)", expanded=False):
        uploaded = st.file_uploader(
            "เลือกไฟล์ Excel ของแผนสอบเทียบ",
            type=["xlsx", "xls"],
            key="cal_plan_upload",
        )
        if uploaded is not None:
            df_new = import_calibration_from_uploaded(uploaded)
            if df_new.empty:
                st.error("ไม่สามารถอ่านข้อมูลจากไฟล์ที่อัปโหลดได้ กรุณาตรวจสอบรูปแบบไฟล์อีกครั้ง")
            else:
                save_calibration_plan(df_new)
                st.info("ระบบจะใช้ไฟล์ใหม่นี้สำหรับแผนสอบเทียบต่อไป")
                st.rerun()

        cal_file_in_use: Path | None = None
        if CAL_PLAN_SIMPLE_PATH.exists():
            cal_file_in_use = CAL_PLAN_SIMPLE_PATH
        elif (DATA_DIR / CAL_ORIGINAL_NAME).exists():
            cal_file_in_use = DATA_DIR / CAL_ORIGINAL_NAME

        if cal_file_in_use:
            st.caption(f"ไฟล์ที่ใช้งานอยู่: **{cal_file_in_use.name}**")
        else:
            st.caption("ยังไม่มีไฟล์แผนสอบเทียบในโฟลเดอร์ data")

    # ----------------- โหลดข้อมูลแผนสอบเทียบ -----------------
    df = load_calibration_plan()
    if df.empty:
        st.info(
            "ยังไม่มีข้อมูลแผนสอบเทียบ ให้คัดลอกไฟล์ 'แผนสอบเทียบและบำรุงรักษาเครื่องมือ.xlsx' "
            "มาไว้ในโฟลเดอร์ data หรืออัปโหลดจากส่วนด้านบน"
        )
        return

    # ---- หาคอลัมน์กำหนดสอบเทียบ (Due M/D/Y) ----
    due_col = "Due M/D/Y"
    if due_col not in df.columns:
        for c in df.columns:
            if isinstance(c, str) and "Due" in c:
                due_col = c
                break
        else:
            st.warning("ไม่พบคอลัมน์กำหนดสอบเทียบ (Due M/D/Y) ในไฟล์แผนสอบเทียบ")
            return

    df[due_col] = pd.to_datetime(df[due_col], errors="coerce")
    today = pd.to_datetime(pd.Timestamp.today().normalize())
    df["days_left"] = (df[due_col] - today).dt.days

    # ===================================================================
    # 🗓 ปฏิทินเดือนปัจจุบัน + เดือนหน้า จาก "ตารางทวนสอบ" (คอลัมน์ 1–12)
    # ===================================================================
    month_cols: list[tuple[int, str]] = []
    for c in df.columns:
        s = str(c).strip()
        if s.isdigit():
            m = int(s)
            if 1 <= m <= 12:
                month_cols.append((m, c))
    month_cols.sort(key=lambda x: x[0])

    current_month = int(today.month)
    current_year = int(today.year)
    next_month = 1 if current_month == 12 else current_month + 1
    next_year = current_year + 1 if current_month == 12 else current_year

    THAI_MONTH_SHORT = {
        1: "ม.ค.",
        2: "ก.พ.",
        3: "มี.ค.",
        4: "เม.ย.",
        5: "พ.ค.",
        6: "มิ.ย.",
        7: "ก.ค.",
        8: "ส.ค.",
        9: "ก.ย.",
        10: "ต.ค.",
        11: "พ.ย.",
        12: "ธ.ค.",
    }

    weekday_labels = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]

    def render_month_plan(container, target_month: int, target_year: int):
        """
        แสดงปฏิทิน + รายการเครื่องมือของเดือน target_month
        - ปฏิทินด้านบน (ในกล่องขาว) เน้นวันที่มี Due Date
        - รายการเครื่องมือ (รูปที่ 2) แสดงด้านล่างในกล่องเดียวกัน
        """
        month_label = THAI_MONTH_SHORT.get(target_month, str(target_month))

        # หา column ที่ตรงกับเดือนนี้ (เช่น เดือน 9 → คอลัมน์ '9')
        col_name = None
        for m, col in month_cols:
            if m == target_month:
                col_name = col
                break

        with container:
            st.markdown('<div class="mem-cal-column">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="mem-cal-column-title">เดือน {month_label} {target_year}</div>'
                '<div class="mem-cal-column-sub">'
                'ดึงจากตารางทวนสอบ (คอลัมน์เดือน 1–12) และ Due Date ของแผนสอบเทียบ '
                'เพื่อแสดงปฏิทินและรายการเครื่องมือของเดือนนี้</div>',
                unsafe_allow_html=True,
            )

            if col_name is None:
                st.markdown(
                    '<div class="mem-cal-empty">ไฟล์นี้ยังไม่มีคอลัมน์ของเดือนนี้ในตารางทวนสอบ</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
                return

            series_m = df[col_name]

            # ค่าที่ไม่ใช่ 0 / ไม่ว่าง / ไม่ None → ถือว่ามีแผนสอบเทียบ
            if pd.api.types.is_numeric_dtype(series_m):
                mask = series_m.fillna(0) > 0
            else:
                s = series_m.astype(str).str.strip()
                mask = (
                    s.notna()
                    & (s != "")
                    & (s != "0")
                    & (s.str.lower() != "none")
                )

            month_df = df[mask].copy()

            # ===== ปฏิทินด้านบนในกล่อง =====
            # วันที่ที่มี Due Date ในเดือนนี้
            highlight_days: set[int] = set()
            if not month_df.empty and due_col in month_df.columns:
                due_series = pd.to_datetime(month_df[due_col], errors="coerce")
                due_series = due_series[
                    (due_series.dt.month == target_month)
                    & (due_series.dt.year == target_year)
                ]
                highlight_days = set(
                    due_series.dropna().dt.day.astype(int).tolist()
                )

            cal_obj = pycal.Calendar(firstweekday=0)  # Monday-first
            weeks = cal_obj.monthdayscalendar(target_year, target_month)

            cal_html = '<div class="mem-cal-calendar"><table class="mem-cal-grid"><thead><tr>'
            for w in weekday_labels:
                cal_html += f"<th>{w}</th>"
            cal_html += "</tr></thead><tbody>"

            for week in weeks:
                cal_html += "<tr>"
                for day in week:
                    if day == 0:
                        cal_html += "<td></td>"
                    else:
                        cls = "mem-cal-day"
                        if day in highlight_days:
                            cls += " mem-cal-day-event"
                        cal_html += f'<td><div class="{cls}">{day}</div></td>'
                cal_html += "</tr>"
            cal_html += "</tbody></table></div>"

            st.markdown(cal_html, unsafe_allow_html=True)

            # ===== รายการเครื่องมือ (รูปที่ 2) =====
            if month_df.empty:
                st.markdown(
                    '<div class="mem-cal-empty">เดือนนี้ยังไม่มีการสอบเทียบจากตารางทวนสอบ</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
                return

            for _, r in month_df.iterrows():
                equip = str(r.get("Equipment", "-"))
                code = str(r.get("ID Code", "-"))
                sn = str(r.get("S/N", "-"))
                note = str(r.get("หมายเหตุ", "-")) if "หมายเหตุ" in month_df.columns else "-"
                due = r.get(due_col)
                if pd.isna(due):
                    due_str = "ไม่ระบุ"
                else:
                    due_str = due.strftime("%d/%m/%Y")

                html_item = f"""
                <div class="mem-cal-item">
                    <div class="mem-cal-item-title">{equip}</div>
                    <div class="mem-cal-item-meta">ID: {code} | S/N: {sn}</div>
                    <div class="mem-cal-item-duedate">กำหนดสอบเทียบ: {due_str}</div>
                    <div class="mem-cal-item-meta">หมายเหตุ: {note}</div>
                </div>
                """
                st.markdown(html_item, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    if month_cols:
        st.markdown(
            """
            <div class="mem-card">
                <div class="mem-card-title">ปฏิทินแผนสอบเทียบ (เดือนปัจจุบันและเดือนหน้า)</div>
                <div class="mem-card-subtitle">
                    ใช้ข้อมูลจากตารางทวนสอบ (คอลัมน์เดือน 1–12) และ Due Date ของไฟล์แผนสอบเทียบ
                    แสดงปฏิทินในกล่องด้านบน และรายการเครื่องมือในเดือนนั้นในกล่องเดียวกัน
                </div>
            """,
            unsafe_allow_html=True,
        )

        col_curr, col_next = st.columns(2)
        render_month_plan(col_curr, current_month, current_year)
        render_month_plan(col_next, next_month, next_year)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(
            "ไฟล์แผนสอบเทียบนี้ยังไม่มีคอลัมน์เดือน (1–12) สำหรับใช้ทำปฏิทิน "
            "หากต้องการใช้ฟังก์ชันนี้ให้เพิ่มตารางทวนสอบที่มีคอลัมน์เลขเดือนก่อน"
        )

    # ===================================================================
    # สถานะตาม Due M/D/Y (ใช้ทำสรุปตัวเลขด้านล่าง)
    # ===================================================================
    def label_status(days):
        if pd.isna(days):
            return "ไม่มีข้อมูล"
        days_int = int(days)
        if days_int < 0:
            return "เลยกำหนดสอบเทียบ"
        if days_int <= 30:
            return "ใกล้ถึงกำหนดสอบเทียบ"
        if days_int <= 90:
            return "ใกล้ถึงกำหนด PM"
        return "พร้อมใช้งาน"

    df["สถานะกำหนด"] = df["days_left"].apply(label_status)

    # --- การ์ดสรุปสถิติ ---
    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">สรุปสถิติการสอบเทียบและบำรุงรักษา</div>
            <div class="mem-card-subtitle">
                ใช้กำหนดวันสอบเทียบ (Due M/D/Y) ในการแบ่งกลุ่มรายการที่เลยกำหนด ใกล้ครบกำหนด และยังพร้อมใช้งาน
            </div>
        """,
        unsafe_allow_html=True,
    )

    overdue_cnt = int((df["สถานะกำหนด"] == "เลยกำหนดสอบเทียบ").sum())
    near_cal_cnt = int((df["สถานะกำหนด"] == "ใกล้ถึงกำหนดสอบเทียบ").sum())
    near_pm_cnt = int((df["สถานะกำหนด"] == "ใกล้ถึงกำหนด PM").sum())
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
        <div class="mem-cal-summary-label">กำหนดในอีก 31–90 วัน (มองเป็นรอบ PM)</div>
      </div>
      <div class="mem-cal-summary-card">
        <div class="mem-cal-summary-value" style="color:#22C55E;">{ready_cnt}</div>
        <div class="mem-cal-summary-label">พร้อมใช้งาน (เกิน 90 วันขึ้นไป)</div>
      </div>
    </div>
    """
    st.markdown(summary_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- ตารางแก้ไขได้ทั้งหมด ---
    st.markdown("### แผนสอบเทียบทั้งหมด (แก้ไขได้)")
    editable_cols = [c for c in df.columns if c not in ("days_left", "สถานะกำหนด")]
    edited_df = st.data_editor(
        df[editable_cols],
        key="cal_plan_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    if st.button("💾 บันทึกแผนสอบเทียบทั้งหมด", use_container_width=True):
        save_calibration_plan(edited_df)
        st.rerun()

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
        if menu_button("แผนสอบเทียบ"):
            st.session_state.current_menu = "แผนสอบเทียบ"
            st.rerun()
        if menu_button("รายงานสรุป"):
            st.session_state.current_menu = "รายงานสรุป"
            st.rerun()

        st.write("")
        if st.button("Logout", type="primary", use_container_width=True):
            keep_keys = []
            for k in list(st.session_state.keys()):
                if k not in keep_keys:
                    del st.session_state[k]
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
