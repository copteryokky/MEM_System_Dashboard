import os
import calendar
from datetime import datetime

import altair as alt
import pandas as pd
import qrcode
import streamlit as st
from io import BytesIO
from pathlib import Path

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH
from auth import (
    authenticate_user,
    register_user,
    get_user_display_name,
    get_user_role,
)

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

# ✅ URL พื้นฐานของแอปสำหรับฝังใน QR (แก้เป็นของตัวเองได้)
APP_QR_BASE_URL = "https://mem-system-dashboard.streamlit.app"

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
MAINT_IMAGE_COL = "รูปภาพประกอบการแจ้งซ่อม"  # ✅ เพิ่มคอลัมน์เก็บรูปจากผู้ใช้

MAINT_EVAL_CHOICES = [
    "ยังไม่ประเมิน",
    "ซ่อมได้ - อยู่ระหว่างดำเนินการ",
    "ซ่อมไม่ได้ - เสนอปลดระวาง/ทดแทน",
]

# ---- CONFIG สำหรับแผนสอบเทียบ ----
CAL_PLAN_SIMPLE_NAME = "calibration_plan_simple.xlsx"
CAL_PLAN_SIMPLE_PATH = DATA_DIR / CAL_PLAN_SIMPLE_NAME
CAL_ORIGINAL_NAME = "แผนสอบเทียบและบำรุงรักษาเครื่องมือ.xlsx"

# ====================================================================
# STYLE: Landing
# ====================================================================
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

# ====================================================================
# STYLE: Login / Register
# ====================================================================
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

# ====================================================================
# STYLE: Main app
# ====================================================================
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
            background: #FFFFFF;
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

        .cal-calendar-wrapper{
            margin-top:8px;
        }
        .cal-grid{
            display:flex;
            flex-direction:column;
            gap:4px;
            font-size:11px;
        }
        .cal-grid-row{
            display:grid;
            grid-template-columns:repeat(7,1fr);
            gap:4px;
        }
        .cal-cell{
            background:#F9FAFB;
            border-radius:10px;
            min-height:34px;
            padding:4px 2px;
            position:relative;
            text-align:center;
            box-shadow:inset 0 0 0 1px #E5E7EB;
        }
        .cal-grid-header .cal-cell{
            background:transparent;
            box-shadow:none;
            font-weight:700;
            color:#6B7280;
        }
        .cal-day-num{
            display:block;
            font-size:11px;
            font-weight:600;
            color:#111827;
        }
        .cal-cell.has-event{
            background:linear-gradient(135deg,#DBEAFE,#EEF2FF);
            box-shadow:0 0 0 1px rgba(37,99,235,0.35);
        }
        .cal-event-badge{
            position:absolute;
            bottom:3px;
            right:4px;
            font-size:9px;
            padding:1px 5px;
            border-radius:999px;
            background:#1D4ED8;
            color:#FFFFFF;
        }


        .cal-event-dot{
            position:absolute;
            top:5px;
            left:5px;
            width:8px;
            height:8px;
            border-radius:999px;
            background:#F97316;
            box-shadow:0 0 0 2px rgba(249,115,22,0.22);
        }
        .cal-legend{
            display:flex;
            flex-wrap:wrap;
            gap:8px;
            font-size:11px;
            margin-top:10px;
            margin-bottom:6px;
        }
        .cal-legend-item{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding:4px 10px;
            border-radius:999px;
            background:#ffffff;
            border:1px solid #e5e7eb;
            color:#4b5563;
        }
        .cal-legend-dot{
            width:10px;
            height:10px;
            border-radius:999px;
            background:#F97316;
            box-shadow:0 0 0 2px rgba(249,115,22,0.18);
        }
        .cal-legend-badge{
            display:inline-flex;
            align-items:center;
            justify-content:center;
            min-width:18px;
            height:16px;
            padding:0 6px;
            border-radius:999px;
            background:#1D4ED8;
            color:#fff;
            font-size:10px;
            font-weight:700;
        }


        .cal-equip-container{
            margin-top:12px;
        }
        .cal-equip-header{
            display:flex;
            justify-content:space-between;
            align-items:center;
            margin-bottom:8px;
            gap:12px;
            flex-wrap:wrap;
        }
        .cal-equip-title-main{
            font-size:16px;
            font-weight:700;
            color:#111827;
        }
        .cal-equip-sub{
            font-size:12px;
            color:#6B7280;
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

# ====================================================================
# Excel helpers (ครุภัณฑ์)
# ====================================================================
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
        if MAINT_IMAGE_COL not in df.columns:  # ✅ สร้างคอลัมน์รูปภาพแจ้งซ่อมถ้ายังไม่มี
            df[MAINT_IMAGE_COL] = ""

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

# ====================================================================
# Helpers สำหรับ "แจ้งซ่อม / บำรุงรักษา"
# ====================================================================
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
    if "สถานะแจ้งซ่อม" not in df.columns:
        return df, 0
    if MAINT_REQUEST_DATE_COL not in df.columns:
        return df, 0

    df_new = df.copy()
    req_dates = pd.to_datetime(df_new[MAINT_REQUEST_DATE_COL], errors="coerce")
    today = pd.to_datetime(pd.Timestamp.today().normalize())
    days_diff = (today - req_dates).dt.days

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
    if MAINT_IMAGE_COL in df_new.columns:
        df_new.loc[mask_expire, MAINT_IMAGE_COL] = ""

    return df_new, expired_count

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

# ====================================================================
# Helpers สำหรับ "แผนสอบเทียบ"
# ====================================================================
def parse_calibration_from_file(path: Path) -> pd.DataFrame:
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base_cols = [c for c in df.columns if c not in ("days_left", "สถานะกำหนด")]
    df_to_save = df[base_cols].copy()
    try:
        df_to_save.to_excel(CAL_PLAN_SIMPLE_PATH, index=False)
        st.success(f"บันทึกแผนสอบเทียบลงไฟล์: {CAL_PLAN_SIMPLE_NAME} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์แผนสอบเทียบ: {e}")

def import_calibration_from_uploaded(uploaded_file) -> pd.DataFrame:
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

# ====================================================================
# รูป & QR helpers
# ====================================================================
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

def get_maint_image_path_from_row(row: pd.Series) -> Path | None:
    """คืน path ของรูปภาพประกอบการแจ้งซ่อมจากข้อมูลในแถว (ถ้ามี)"""
    val = str(row.get(MAINT_IMAGE_COL, "") or "").strip()
    if not val:
        return None
    p = Path(val)
    if not p.is_absolute():
        p = IMAGE_DIR / p.name
    return p

def save_maint_image(uploaded, asset_code: str) -> str:
    """บันทึกรูปภาพที่ผู้ใช้แนบตอนแจ้งซ่อม"""
    suffix = Path(uploaded.name).suffix or ".png"
    safe_code = asset_code.replace("/", "_").replace("\\", "_").replace(" ", "_")
    filename = f"{safe_code}_maint_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
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

# ====================================================================
# Landing page
# ====================================================================
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
        st.rerun()

# ====================================================================
# QR public page (อ่านอย่างเดียวเมื่อยังไม่ล็อกอิน)
# ====================================================================
def qr_public_page():
    set_main_style()

    # ดึง code จาก session หรือ query param
    code = st.session_state.get("qr_code_from_url")
    if not code:
        params = st.session_state.get("_url_params", {})
        if isinstance(params, dict) and "code" in params:
            v = params["code"]
            code = v[0] if isinstance(v, list) else v

    st.markdown(
        '<div class="mem-page-title">รายละเอียดครุภัณฑ์จาก QR Code</div>',
        unsafe_allow_html=True,
    )
    if not code:
        st.info("ไม่พบรหัสครุภัณฑ์จาก QR Code (parameter 'code')")
        if st.button("กลับไปหน้าแรก", use_container_width=True):
            st.session_state.view = "landing"
            st.rerun()
        return

    df = load_equipment_data()
    if df.empty:
        st.warning("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel ที่ใช้งานอยู่")
        return

    if ASSET_CODE_COL not in df.columns:
        st.warning(f"ไม่พบคอลัมน์ '{ASSET_CODE_COL}' ในไฟล์ Excel")
        return

    matches = df[df[ASSET_CODE_COL].astype(str) == str(code)]
    if matches.empty:
        st.error(f"ไม่พบครุภัณฑ์ที่มีรหัส '{code}' ในไฟล์ข้อมูลปัจจุบัน")
        return

    row = matches.iloc[0]
    st.markdown(
        f"""
        <div class="mem-card">
          <div class="mem-card-title">รหัสครุภัณฑ์: {code}</div>
          <div class="mem-card-subtitle">
            ข้อมูลนี้แสดงในโหมดอ่านอย่างเดียว หากต้องการแจ้งซ่อมหรือเขียนหมายเหตุ
            กรุณาเข้าสู่ระบบด้วยบัญชีผู้ใช้ภายใน
          </div>
        """,
        unsafe_allow_html=True,
    )

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
            MAINT_IMAGE_COL,
        )
    ]
    half = (len(columns_list) + 1) // 2
    left_cols = columns_list[:half]
    right_cols = columns_list[half:]

    col_left, col_right = st.columns(2)
    with col_left:
        for col_name in left_cols:
            current_val = row.get(col_name, "")
            st.text_input(
                str(col_name),
                value="" if pd.isna(current_val) else str(current_val),
                key=f"qr_public_left_{col_name}",
                disabled=True,
            )
    with col_right:
        for col_name in right_cols:
            current_val = row.get(col_name, "")
            st.text_input(
                str(col_name),
                value="" if pd.isna(current_val) else str(current_val),
                key=f"qr_public_right_{col_name}",
                disabled=True,
            )

    st.markdown("### สถานะแจ้งซ่อมปัจจุบัน")
    st.write(str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or MAINT_STATUS_CHOICES[0]))

    st.markdown("### หมายเหตุการซ่อม (อ่านอย่างเดียว)")
    st.text_area(
        "หมายเหตุการซ่อม",
        value=str(row.get(MAINT_NOTE_COL, "") or ""),
        key="qr_public_note",
        disabled=True,
    )

    st.info("หากต้องการแจ้งซ่อม / เขียนหมายเหตุ กรุณาเข้าสู่ระบบก่อน")

    if st.button("เข้าสู่ระบบเพื่อแจ้งซ่อม / เขียนหมายเหตุ", use_container_width=True):
        st.session_state.qr_code_pending = str(code)
        st.session_state.view = "login"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ====================================================================
# Login page
# ====================================================================
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

    register_clicked = st.button("📝 สมัครใช้งานใหม่", use_container_width=True)
    back_clicked = st.button("⬅️ กลับไปหน้าแรก", use_container_width=True)

    st.markdown(
        '<div class="mem-login-footer">บัญชีใหม่จะมีสิทธิ์ดูรายการครุภัณฑ์ และแจ้งซ่อม/เขียนหมายเหตุได้เท่านั้น หากต้องการสิทธิ์ admin กรุณาติดต่อผู้ดูแลระบบ</div>',
        unsafe_allow_html=True,
    )

    if register_clicked:
        st.session_state.view = "register"
        st.rerun()

    if back_clicked:
        st.session_state.view = "landing"
        st.session_state.logged_in = False
        st.rerun()

    if login_clicked:
        ok, display_name = authenticate_user(username, password)
        if ok:
            role = get_user_role(username) or "user"

            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.display_name = display_name or username
            st.session_state.role = role

            # ถ้ามี QR pending / code จาก URL ให้ไปหน้า "รายการครุภัณฑ์"
            pending_code = st.session_state.get("qr_code_pending")
            if pending_code:
                st.session_state.qr_code_from_url = str(pending_code)

            if st.session_state.get("qr_code_from_url"):
                st.session_state.current_menu = "รายการครุภัณฑ์"
            else:
                st.session_state.current_menu = (
                    "หน้าหลัก" if role == "admin" else "รายการครุภัณฑ์"
                )

            st.session_state.view = "app"

            # 🔒===============================
            #  F5 persistence: ใส่ user (+code ถ้ามี) ลง URL เสมอ
            #  ใช้ experimental_set_query_params อย่างเดียวให้ชัวร์
            # ===============================#
            try:
                code_for_url = st.session_state.get("qr_code_from_url")
                if code_for_url:
                    st.experimental_set_query_params(
                        user=username,
                        code=str(code_for_url),
                    )
                else:
                    st.experimental_set_query_params(user=username)
            except Exception:
                # ถ้าเซ็ตไม่ได้ ก็ยังใช้ session เดิมได้ แต่ F5 จะไม่ช่วย
                pass
            # ===============================#

            st.session_state.qr_code_pending = None
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")

# ====================================================================
# Register page
# ====================================================================
def register_page():
    set_login_style()

    st.markdown('<div class="mem-login-title">สมัครใช้งานระบบ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mem-login-sub">สร้างบัญชีผู้ใช้ใหม่สำหรับแจ้งซ่อมและดูรายการครุภัณฑ์</div>',
        unsafe_allow_html=True,
    )

    username = st.text_input("👤 ชื่อผู้ใช้ (ใช้สำหรับเข้าสู่ระบบ)", key="reg_username")
    display_name = st.text_input("ชื่อ-สกุล / ชื่อที่แสดงในระบบ", key="reg_display_name")
    password = st.text_input("🔐 รหัสผ่าน", type="password", key="reg_password")
    password2 = st.text_input("🔐 ยืนยันรหัสผ่าน", type="password", key="reg_password2")

    col1, col2 = st.columns(2)
    with col1:
        create_clicked = st.button("สร้างบัญชี", use_container_width=True)
    with col2:
        back_clicked = st.button("กลับไปหน้าเข้าสู่ระบบ", use_container_width=True)

    if back_clicked:
        st.session_state.view = "login"
        st.rerun()

    if create_clicked:
        if not username or not password:
            st.warning("กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบ")
            return
        if password != password2:
            st.warning("รหัสผ่านและยืนยันรหัสผ่านไม่ตรงกัน")
            return

        success, msg = register_user(username, password, display_name)
        if success:
            st.success(msg + " สามารถเข้าสู่ระบบได้ทันทีด้วยชื่อผู้ใช้และรหัสผ่านที่สร้างไว้")
            st.session_state.view = "login"
            st.rerun()
        else:
            st.error(msg)

# ====================================================================
# Helper: Altair style
# ====================================================================
def styled_chart(chart: alt.Chart, width: int, height: int) -> alt.Chart:
    return (
        chart.properties(width=width, height=height)
        .configure_view(
            stroke="#E5E7EB",
            strokeWidth=1,
            fill="#FFFFFF",
        )
    )

# ====================================================================
# หน้า "หน้าหลัก" (admin เท่านั้น)
# ====================================================================
def page_home():
    set_main_style()

    role = st.session_state.get("role", "user")
    if role != "admin":
        st.warning("หน้านี้สำหรับผู้ดูแลระบบเท่านั้น")
        return

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
        st.info("ยังไม่มีข้อมูลครุภัณฑ์ในไฟล์ Excel ที่ใช้งานอยู่")
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

# ====================================================================
# ตาราง + เลือกแถว (ใช้เฉพาะ admin)
# ====================================================================
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

# ====================================================================
# หน้า "รายการครุภัณฑ์" (admin กับ user แสดงไม่เหมือนกัน)
# ====================================================================
def page_equipment_list():
    set_main_style()

    role = st.session_state.get("role", "user")
    is_admin = role == "admin"

    st.markdown(
        '<div class="mem-page-title">รายการครุภัณฑ์</div>',
        unsafe_allow_html=True,
    )

    files = get_available_excel_files()
    init_excel_file_name()
    current_name = st.session_state.get("excel_file_name")

    if is_admin:
        st.markdown("### เลือกไฟล์ Excel ที่ต้องการใช้งาน")

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
    else:
        path = get_current_excel_path()
        if path is None or not path.exists():
            st.info("ผู้ดูแลระบบยังไม่ได้เตรียมไฟล์ข้อมูลครุภัณฑ์สำหรับใช้งาน")
        else:
            st.caption(f"กำลังดึงข้อมูลจากไฟล์ที่ผู้ดูแลระบบตั้งค่าไว้: **{path.name}**")

    df = load_equipment_data()
    if df.empty:
        st.info("ยังไม่มีข้อมูลในไฟล์ Excel ที่เลือกอยู่")
        return

    # ---------- ถ้ามี code จาก QR ให้เลือกแถวให้เอง ----------
    qr_code = st.session_state.get("qr_code_from_url")
    qr_match_index = None
    if qr_code and ASSET_CODE_COL in df.columns:
        try:
            qr_matches = df.index[df[ASSET_CODE_COL].astype(str) == str(qr_code)].tolist()
        except Exception:
            qr_matches = []
        if qr_matches:
            qr_match_index = qr_matches[0]
            st.session_state.selected_row_idx = qr_match_index
            st.markdown(
                f"""
                <div class="mem-card" style="padding:12px 18px;margin-bottom:18px;">
                  <div class="mem-card-title" style="font-size:16px;">
                    เปิดจาก QR Code – รหัสครุภัณฑ์ {qr_code}
                  </div>
                  <div class="mem-card-subtitle">
                    ระบบกำลังแสดงรายละเอียดของครุภัณฑ์ที่สแกนจาก QR Code นี้
                    หากเปลี่ยนการเลือกในช่องด้านล่าง ระบบจะย้ายไปยังรายการอื่นตามที่เลือก
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(f"ไม่พบครุภัณฑ์ที่มีรหัส {qr_code} ในไฟล์ Excel ปัจจุบัน")

    # ------------------------------ admin mode ------------------------------
    if is_admin:
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

        def format_option_admin(i: int) -> str:
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
            format_func=format_option_admin,
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
                MAINT_IMAGE_COL,
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

        st.markdown("### หมายเหตุการซ่อม")
        current_note = str(row.get(MAINT_NOTE_COL, "") or "")
        maint_note_admin = st.text_area(
            "หมายเหตุการซ่อม (อธิบายสาเหตุ / รายละเอียดการซ่อม)",
            value=current_note,
            key=f"maint_note_admin_{selected_idx}",
        )
        updated_values[MAINT_NOTE_COL] = maint_note_admin

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
                # ใช้ URL ของแอปเดียวกัน พร้อม parameter code
                url_for_qr = f"{APP_QR_BASE_URL}/?code={asset_code}"
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

    # ------------------------------ normal user mode ------------------------------
    else:
        st.markdown("### ตารางรายการครุภัณฑ์ (โหมดอ่านอย่างเดียว)")
        view_cols = [c for c in df.columns if c != "รูปภาพครุภัณฑ์"]
        st.dataframe(
            df[view_cols],
            hide_index=True,
            use_container_width=True,
        )

        st.markdown("---")

        def format_option_user(i: int) -> str:
            row = df.iloc[i]
            name = str(row.get("ชื่อ", "ไม่ทราบชื่อ"))
            code = str(row.get(ASSET_CODE_COL, ""))
            return f"{i+1:03d} - {name} ({code})"

        options_index = list(df.index)
        default_idx = st.session_state.get("selected_row_idx", 0)
        if default_idx >= len(df):
            default_idx = 0

        selected_idx_box = st.selectbox(
            "เลือกครุภัณฑ์ที่ต้องการดูรายละเอียด / แจ้งซ่อม",
            options=options_index,
            index=default_idx,
            format_func=format_option_user,
            key="equip_select_box_user",
        )

        if selected_idx_box != st.session_state.get("selected_row_idx", 0):
            st.session_state.selected_row_idx = selected_idx_box
            st.rerun()

        selected_idx = st.session_state.get("selected_row_idx", 0)
        if selected_idx >= len(df):
            selected_idx = 0

        row = df.iloc[selected_idx].copy()
        asset_code = str(row.get(ASSET_CODE_COL, ""))

        st.markdown("### รายละเอียดครุภัณฑ์ (อ่านอย่างเดียว)")
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
                MAINT_IMAGE_COL,
            )
        ]
        half = (len(columns_list) + 1) // 2
        left_cols = columns_list[:half]
        right_cols = columns_list[half:]

        col_left, col_right = st.columns(2)

        with col_left:
            for col_name in left_cols:
                current_val = row.get(col_name, "")
                st.text_input(
                    str(col_name),
                    value="" if pd.isna(current_val) else str(current_val),
                    key=f"detail_left_view_{col_name}_{selected_idx}",
                    disabled=True,
                )

        with col_right:
            for col_name in right_cols:
                current_val = row.get(col_name, "")
                st.text_input(
                    str(col_name),
                    value="" if pd.isna(current_val) else str(current_val),
                    key=f"detail_right_view_{col_name}_{selected_idx}",
                    disabled=True,
                )

        st.markdown("### แจ้งซ่อม / บันทึกหมายเหตุ (สำหรับผู้ใช้ทั่วไป)")

        current_maint = str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or "")
        if current_maint not in MAINT_STATUS_CHOICES:
            current_maint = MAINT_STATUS_CHOICES[0]

        st.write(f"**สถานะแจ้งซ่อมปัจจุบัน:** {current_maint}")

        note_default = str(row.get(MAINT_NOTE_COL, "") or "")
        note_user = st.text_area(
            "เขียนรายละเอียด / สาเหตุที่แจ้งซ่อม",
            value=note_default,
            key=f"maint_note_user_{selected_idx}",
        )

        # ✅ ส่วนอัปโหลดรูปภาพประกอบการแจ้งซ่อม
        st.markdown("#### รูปภาพประกอบการแจ้งซ่อม (ถ้ามี)")

        current_maint_image_path = None
        if MAINT_IMAGE_COL in df.columns:
            current_maint_image_path = get_maint_image_path_from_row(row)

        if current_maint_image_path and current_maint_image_path.exists():
            st.image(
                str(current_maint_image_path),
                caption="รูปภาพประกอบการแจ้งซ่อมล่าสุด",
                use_column_width=True,
            )

        uploaded_maint_img = st.file_uploader(
            "อัปโหลดรูปภาพประกอบการแจ้งซ่อม (เช่น รูปตำแหน่งที่เสีย, หน้าจอ error)",
            type=["png", "jpg", "jpeg"],
            key=f"maint_img_user_{selected_idx}",
        )

        if uploaded_maint_img is not None:
            st.image(
                uploaded_maint_img,
                caption="ตัวอย่างรูปที่จะส่งไปกับคำขอแจ้งซ่อม",
                use_column_width=True,
            )

        if st.button("📩 ส่งคำขอแจ้งซ่อม / บันทึกหมายเหตุ", use_container_width=True):
            df_current = load_equipment_data()
            if selected_idx not in df_current.index:
                st.error("ไม่พบแถวข้อมูลนี้ในไฟล์แล้ว กรุณารีเฟรชหน้า")
            else:
                today_date = datetime.today().date()
                df_current.at[selected_idx, "สถานะแจ้งซ่อม"] = "แจ้งซ่อมแล้ว - กำลังดำเนินการ"
                df_current.at[selected_idx, MAINT_REQUEST_DATE_COL] = today_date
                df_current.at[selected_idx, MAINT_NOTE_COL] = note_user

                if MAINT_EST_DAYS_COL in df_current.columns:
                    if (
                        pd.isna(df_current.at[selected_idx, MAINT_EST_DAYS_COL])
                        or df_current.at[selected_idx, MAINT_EST_DAYS_COL] in ("", None)
                    ):
                        df_current.at[selected_idx, MAINT_EST_DAYS_COL] = 7

                # ✅ บันทึกไฟล์รูปภาพประกอบการแจ้งซ่อม (ถ้ามี)
                if uploaded_maint_img is not None:
                    filename = save_maint_image(uploaded_maint_img, asset_code)
                    if MAINT_IMAGE_COL not in df_current.columns:
                        df_current[MAINT_IMAGE_COL] = ""
                    df_current.at[selected_idx, MAINT_IMAGE_COL] = filename

                save_equipment_data(df_current)
                st.success(
                    "บันทึกคำขอแจ้งซ่อมและหมายเหตุเรียบร้อยแล้ว พร้อมรูปภาพประกอบ (ถ้ามี) ระบบอัปเดตแบบ Real-time"
                )
                st.rerun()

# ====================================================================
# หน้า "แจ้งซ่อม / บำรุงรักษา" (admin)
# ====================================================================
def page_maintenance():
    set_main_style()

    role = st.session_state.get("role", "user")
    if role != "admin":
        st.warning("หน้านี้สำหรับผู้ดูแลระบบเท่านั้น ผู้ใช้ทั่วไปให้แจ้งซ่อมผ่านหน้า 'รายการครุภัณฑ์' หรือสแกน QR")
        return

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
        MAINT_IMAGE_COL,  # ✅ ensure คอลัมน์รูปภาพแจ้งซ่อม
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

    maint_counts = build_maintenance_summary(df)

    st.markdown(
        """
        <div class="mem-card">
            <div class="mem-card-title">ภาพรวมสถานะแจ้งซ่อม</div>
            <div class="mem-card-subtitle">
                แสดงจำนวนครุภัณฑ์ตามสถานะแจ้งซ่อม ดึงข้อมูลจากไฟล์ Excel เดียวกับหน้า QR
                เมื่อมีการแจ้งซ่อมหรือเปลี่ยนสถานะจากหน้า QR / หน้า user ข้อมูลในหน้านี้จะอัปเดตอัตโนมัติ
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
        # เพิ่ม flag "ใหม่วันนี้" สำหรับแจ้งซ่อมใหม่ (real-time indicator)
        today_date = datetime.today().date()
        new_mask = timers_df["วันที่แจ้งซ่อมล่าสุด"].astype("datetime64[ns]").dt.date == today_date
        timers_df["ใหม่วันนี้"] = ["⭐" if x else "" for x in new_mask]
        new_count = int(new_mask.sum())
        if new_count > 0:
            st.success(f"มีคำขอแจ้งซ่อมใหม่วันนี้ {new_count} รายการ (แสดงด้วยสัญลักษณ์ ⭐ ในตาราง)")

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

        # ✅ แสดงรูปภาพประกอบการแจ้งซ่อมจากผู้ใช้ ถ้ามี
        st.markdown("#### รูปภาพประกอบการแจ้งซ่อมจากผู้ใช้")
        maint_img_path = get_maint_image_path_from_row(row_sel)
        if maint_img_path and maint_img_path.exists():
            st.image(
                str(maint_img_path),
                caption="รูปภาพประกอบการแจ้งซ่อมล่าสุดจากผู้ใช้",
                use_column_width=True,
            )
        else:
            st.caption("ยังไม่มีรูปภาพประกอบการแจ้งซ่อมสำหรับรายการนี้")

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

                if eval_select.startswith("ซ่อมไม่ได้"):
                    df_current.at[selected_idx, "สถานะแจ้งซ่อม"] = "ปลดระวาง / รอจำหน่าย"

                save_equipment_data(df_current)
                st.success("บันทึกข้อมูลแจ้งซ่อมเรียบร้อยแล้ว")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ====================================================================
# helpers สำหรับ page_calibration
# ====================================================================
def _find_col_by_keywords(columns, keywords):
    for c in columns:
        text = str(c).lower()
        if all(k.lower() in text for k in keywords):
            return c
    return None

def _build_calendar_html(year: int, month: int, due_series: pd.Series) -> str:
    """Return HTML calendar for (year, month).

    - Highlights days that have calibration schedules (based on Due Date)
    - Shows an orange dot + blue badge (count) on days with schedules
    """
    if due_series is None:
        due_series = pd.Series([], dtype="datetime64[ns]")

    due_series = pd.to_datetime(due_series, errors="coerce")
    due_this = due_series.dropna()
    due_this = due_this[(due_this.dt.year == year) & (due_this.dt.month == month)]
    day_counts = due_this.dt.day.value_counts().to_dict()

    cal = calendar.Calendar(firstweekday=0)  # Monday
    days_th = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]

    html = ['<div class="cal-calendar-wrapper">']
    html.append('<div class="cal-grid">')

    # Header
    html.append('<div class="cal-grid-row cal-grid-header">')
    for d in days_th:
        html.append(f'<div class="cal-header-cell">{d}</div>')
    html.append("</div>")

    # Weeks
    for week in cal.monthdayscalendar(year, month):
        html.append('<div class="cal-grid-row">')
        for day in week:
            if day == 0:
                html.append('<div class="cal-cell empty"></div>')
                continue

            count = int(day_counts.get(day, 0))
            classes = "cal-cell"
            title = ""
            if count > 0:
                classes += " has-event"
                title = f' title="มีแผนสอบเทียบ {count} รายการ"'

            html.append(f'<div class="{classes}"{title}>')
            html.append(f'<span class="cal-day-num">{day}</span>')

            if count > 0:
                # visual marker: dot + count badge
                html.append('<span class="cal-event-dot" aria-hidden="true"></span>')
                html.append(f'<span class="cal-event-badge">{count} รายการ</span>')

            html.append("</div>")
        html.append("</div>")

    html.append("</div></div>")
    return "".join(html)

def _get_month_mask(df: pd.DataFrame, month_cols: list[tuple[int, str]], target_month: int):
    col_name = None
    for m, col in month_cols:
        if m == target_month:
            col_name = col
            break
    if col_name is None or col_name not in df.columns:
        return pd.Series([False] * len(df), index=df.index)

    series_m = df[col_name]

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
    return mask

# ====================================================================
# หน้า "แผนสอบเทียบ" – admin เท่านั้น
# ====================================================================
def page_calibration():
    set_main_style()

    role = st.session_state.get("role", "user")
    if role != "admin":
        st.warning("หน้านี้สำหรับผู้ดูแลระบบเท่านั้น")
        return

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
                st.info("ระบบจะใช้ไฟล์ใหม่นี้สำหรับแผนสอบเทียบทอดไป")
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

    df_raw = load_calibration_plan()
    df = df_raw.copy()
    if df.empty:
        st.info(
            "ยังไม่มีข้อมูลแผนสอบเทียบ ให้คัดลอกไฟล์ 'แผนสอบเทียบและบำรุงรักษาเครื่องมือ.xlsx' "
            "มาไว้ในโฟลเดอร์ data หรืออัปโหลดจากส่วนด้านบน"
        )
        return

    due_col = "Due M/D/Y"
    if due_col not in df.columns:
        for c in df.columns:
            if isinstance(c, str) and "due" in c.lower():
                due_col = c
                break
        else:
            due_col = None

    if due_col is not None and due_col in df.columns:
        df[due_col] = pd.to_datetime(df[due_col], errors="coerce")
    else:
        df[due_col] = pd.NaT

    today = pd.to_datetime(pd.Timestamp.today().normalize())
    df["days_left"] = (df[due_col] - today).dt.days

    month_cols: list[tuple[int, str]] = []
    for c in df.columns:
        s = str(c).strip()
        if s.isdigit():
            m = int(s)
            if 1 <= m <= 12:
                month_cols.append((m, c))
    month_cols.sort(key=lambda x: x[0])

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

        # -------------------------
    # Dual-month calendar (Left = current month, Right = next month)
    # - Left month is always the current month (based on today)
    # - Right month is always the next month (handle year transition)
    # -------------------------
    left_year = today.year
    left_month = int(today.month)
    right_month = 1 if left_month == 12 else left_month + 1
    right_year = left_year + 1 if left_month == 12 else left_year

    if month_cols:
        st.markdown(
            """
            <div class="mem-card">
                <div class="mem-card-title">ปฏิทินแผนสอบเทียบ (2 เดือน)</div>
                <div class="mem-card-subtitle">
                    แสดง 2 เดือนแบบเคียงข้างกันเสมอ: <b>ซ้าย = เดือนปัจจุบัน</b>, <b>ขวา = เดือนถัดไป</b>
                    (รองรับการข้ามปี เช่น ธ.ค. → ม.ค. ปีถัดไป) โดยอิงจาก <b>Due Date</b> ของแต่ละรายการ
                </div>
            """,
            unsafe_allow_html=True,
        )
        # Month selector (left) + auto next month (right)
        # Default = current month/year; user can change month/year normally
        def _next_month(y: int, mo: int):
            return (y + 1, 1) if mo == 12 else (y, mo + 1)

        # Build year options from Due Date range + today (with buffer)
        due_years = (
            pd.to_datetime(df[due_col], errors="coerce").dt.year.dropna()
            if due_col
            else pd.Series([], dtype="float")
        )
        if not due_years.empty:
            y_min = int(due_years.min())
            y_max = int(due_years.max())
        else:
            y_min = int(today.year)
            y_max = int(today.year)

        y_min = min(y_min, int(today.year)) - 1
        y_max = max(y_max, int(today.year)) + 1
        years_list = list(range(y_min, y_max + 1))
        ym_options = [(y, m_) for y in years_list for m_ in range(1, 13)]

        def _fmt_ym(ym):
            y, m_ = ym
            return f"{THAI_MONTH_SHORT.get(int(m_), str(m_))} {int(y) + 543}"

        default_ym = (int(today.year), int(today.month))
        default_index = ym_options.index(default_ym) if default_ym in ym_options else 0

        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            left_ym = st.selectbox(
                "เดือนฝั่งซ้าย (เลือกได้)",
                options=ym_options,
                index=default_index,
                format_func=_fmt_ym,
                key="cal_left_ym",
            )

        left_year, left_month = int(left_ym[0]), int(left_ym[1])
        right_year, right_month = _next_month(left_year, left_month)

        with col_sel2:
            # Right month is always auto next month (locked)
            # Streamlit versions differ: selectbox supports disabled in newer versions
            try:
                st.selectbox(
                    "เดือนฝั่งขวา (เดือนถัดไปอัตโนมัติ)",
                    options=[(right_year, right_month)],
                    index=0,
                    format_func=_fmt_ym,
                    key="cal_right_ym",
                    disabled=True,
                )
            except TypeError:
                st.text_input(
                    "เดือนฝั่งขวา (เดือนถัดไปอัตโนมัติ)",
                    value=_fmt_ym((right_year, right_month)),
                    key="cal_right_ym_text",
                    disabled=True,
                )
        st.markdown(
            """
            <div class="cal-legend">
              <div class="cal-legend-item"><span class="cal-legend-dot"></span> มีแผนสอบเทียบในวันนั้น</div>
              <div class="cal-legend-item"><span class="cal-legend-badge">n</span> จำนวนรายการสอบเทียบ (n รายการ)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_cal1, col_cal2 = st.columns(2)

        def render_calendar(container, year_val: int, month_val: int):
            month_label = THAI_MONTH_SHORT.get(month_val, str(month_val))
            html_calendar = _build_calendar_html(
                year_val,
                month_val,
                df[due_col] if due_col is not None else None,
            )
            with container:
                st.markdown(
                    f"""
                    <div class="mem-cal-column">
                        <div class="mem-cal-column-title">เดือน {month_label} {year_val+543}</div>
                        <div class="mem-cal-column-sub">
                            จุดสีส้ม + ป้ายจำนวนรายการ แสดงวันที่มี Due Date ในเดือนนี้
                        </div>
                        {html_calendar}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        render_calendar(col_cal1, left_year, left_month)
        render_calendar(col_cal2, right_year, right_month)

        st.markdown("</div>", unsafe_allow_html=True)
    else:

        st.info(
            "ไฟล์แผนสอบเทียบนี้ยังไม่มีคอลัมน์เดือน (1–12) สำหรับใช้ทำปฏิทิน "
            "หากต้องการใช้ฟังก์ชันนี้ให้เพิ่มตารางทวนสอบที่มีคอลัมน์เลขเดือนก่อน"
        )

    st.markdown(
        """
        <div class="mem-card">
          <div class="cal-equip-container">
            <div class="cal-equip-header">
              <div>
                <div class="cal-equip-title-main">รายการเครื่องมือในแผนสอบเทียบ</div>
                <div class="cal-equip-sub">
                  ดึงจากตารางทวนสอบ (คอลัมน์เดือน 1–12) และ Due Date ของไฟล์แผนสอบเทียบ
                  เครื่องมือแต่ละรายการจะแสดง ID, S/N, Due Date และหมายเหตุ
                </div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    equip_col = _find_col_by_keywords(df.columns, ["equipment"]) or _find_col_by_keywords(
        df.columns, ["รายการ"]
    )
    id_col = _find_col_by_keywords(df.columns, ["id", "code"]) or _find_col_by_keywords(
        df.columns, ["id"]
    )
    sn_col = _find_col_by_keywords(df.columns, ["s/n"]) or _find_col_by_keywords(
        df.columns, ["serial"]
    )
    note_col = "หมายเหตุ" if "หมายเหตุ" in df.columns else _find_col_by_keywords(
        df.columns, ["note"]
    )
    if month_cols:
        _month_opts_for_cards = [m for m, _ in month_cols]
        _default_idx_for_cards = (
            _month_opts_for_cards.index(left_month)
            if "left_month" in locals() and left_month in _month_opts_for_cards
            else (_month_opts_for_cards.index(int(today.month)) if int(today.month) in _month_opts_for_cards else 0)
        )

        month_for_cards = st.selectbox(
            "เลือกเดือนสำหรับแสดงรายการ",
            options=_month_opts_for_cards,
            index=_default_idx_for_cards,
            format_func=lambda m: THAI_MONTH_SHORT.get(m, str(m)),
            key="cal_month_cards",
        )
        mask_cards = _get_month_mask(df, month_cols, month_for_cards)
        df_cards = df[mask_cards].copy()
    else:
        df_cards = df.copy()

    if df_cards.empty:
        st.info("เดือนนี้ยังไม่มีเครื่องมือในแผนสอบเทียบ")
    else:
        cols_cards = st.columns(2)
        for i, (_, r) in enumerate(df_cards.iterrows()):
            name = str(r.get(equip_col, "-")) if equip_col else "-"
            _id = str(r.get(id_col, "-")) if id_col else "-"
            sn = str(r.get(sn_col, "-")) if sn_col else "-"
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

    st.markdown("### แผนสอบเทียบทั้งหมด (คลิกแถวเพื่อดู/แก้ไขรายละเอียดด้านล่าง)")

    # ใช้ df_view สำหรับแสดงผล, df_raw สำหรับบันทึกกลับไฟล์
    df_view = df.copy().reset_index(drop=True)
    df_raw = df_raw.copy().reset_index(drop=True)

    # -------------------------
    # 3.1 เลือกแถวจากตาราง (พยายามใช้แบบ “คลิกแถว” ก่อน)
    # -------------------------
    selected_row = None
    if df_view.empty:
        st.info("ยังไม่มีข้อมูลแผนสอบเทียบ")
    else:
        # พยายามใช้ st.dataframe ที่รองรับการเลือกแถวด้วยการคลิก (ถ้า Streamlit เวอร์ชันรองรับ)
        try:
            evt = st.dataframe(
                df_view,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="cal_plan_click_table",
            )
            sel_rows = getattr(getattr(evt, "selection", None), "rows", [])
            if sel_rows:
                selected_row = int(sel_rows[0])
        except TypeError:
            # fallback: ใช้ checkbox คอลัมน์ "เลือก" (รองรับ single selection)
            df_select_view = df_view.copy()
            df_select_view.insert(0, "เลือก", False)

            prev = st.session_state.get("cal_selected_rowid", None)
            if prev is not None:
                try:
                    prev_i = int(prev)
                    if 0 <= prev_i < len(df_select_view):
                        df_select_view.loc[prev_i, "เลือก"] = True
                except Exception:
                    pass

            disabled_cols = [c for c in df_select_view.columns if c != "เลือก"]
            selected_table = st.data_editor(
                df_select_view,
                key="cal_plan_selector",
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                disabled=disabled_cols,
            )
            picked = selected_table[selected_table["เลือก"] == True]
            if len(picked) > 0:
                selected_row = int(picked.index[0])

    # อัปเดตค่า selection ใน session_state (ให้ตาราง/ฟอร์ม sync กัน)
    if selected_row is not None:
        st.session_state["cal_selected_rowid"] = selected_row

    # -------------------------
    # เลือกรายการแบบ dropdown (สไตล์เดียวกับหน้า “รายละเอียดครุภัณฑ์”)
    # -------------------------
    def _pick_col(candidates):
        for c in candidates:
            if c in df_raw.columns:
                return c
        return None

    no_col = _pick_col(["No.", "ลำดับ", "No"])
    id_col = _pick_col(["ID Code", "ID", "รหัส", "รหัสครุภัณฑ์", ASSET_CODE_COL])
    name_col = _pick_col(["Equipment", "ชื่อเครื่องมือ", "ชื่อครุภัณฑ์", "ชื่ออุปกรณ์", "รายการ"])
    assetid_col = _pick_col(["Asset ID", "AssetID", "ทะเบียน", "ทะเบียนครุภัณฑ์"])
    manu_col = _pick_col(["Manufacture", "Manufacturer", "ยี่ห้อ", "ผู้ผลิต"])
    model_col = _pick_col(["Models", "Model", "รุ่น"])
    sn_col = _pick_col(["S/N", "SN", "Serial", "Serial No.", "หมายเลขเครื่อง"])
    dept_col = _pick_col(["หน่วยงาน", "แผนก", "ฝ่าย", "Department", "Dept", "แหล่งข้อมูล"])
    vendor_col = _pick_col(["ผู้รับจ้าง", "บริษัท", "Vendor", "ผู้สอบเทียบ", "หน่วยงานภายนอก", "ผู้ให้บริการ"])
    last_col = _pick_col(["Last M/D/Y", "Last Calibration", "วันที่สอบเทียบล่าสุด", "วันสอบเทียบล่าสุด"])
    note_col = _pick_col(["หมายเหตุ", "Note", "Remark", "รายละเอียดเพิ่มเติม"])

    # กัน key ใน session_state ให้ไม่หลุด range
    if df_view.empty:
        rowid = None
    else:
        if "cal_selected_rowid" not in st.session_state:
            st.session_state["cal_selected_rowid"] = 0
        try:
            st.session_state["cal_selected_rowid"] = int(st.session_state["cal_selected_rowid"])
        except Exception:
            st.session_state["cal_selected_rowid"] = 0
        if st.session_state["cal_selected_rowid"] < 0 or st.session_state["cal_selected_rowid"] >= len(df_view):
            st.session_state["cal_selected_rowid"] = 0

        def _label_row(i: int) -> str:
            try:
                r = df_raw.loc[i]
            except Exception:
                return str(i)
            no_v = "" if (no_col is None or pd.isna(r.get(no_col))) else str(r.get(no_col)).strip()
            id_v = "" if (id_col is None or pd.isna(r.get(id_col))) else str(r.get(id_col)).strip()
            nm_v = "" if (name_col is None or pd.isna(r.get(name_col))) else str(r.get(name_col)).strip()
            parts = []
            if no_v and no_v.lower() != "none":
                parts.append(f"{no_v}")
            if nm_v and nm_v.lower() != "none":
                parts.append(nm_v)
            if id_v and id_v.lower() != "none":
                parts.append(f"({id_v})")
            if not parts:
                parts = [f"รายการ {i+1}"]
            return " - ".join(parts[:2]) if len(parts) >= 2 else parts[0]

        st.selectbox(
            "เลือกรายการเพื่อดู/แก้ไขรายละเอียด (เลือกจากตารางด้านบน หรือเลือกจาก dropdown นี้ได้)",
            options=list(range(len(df_view))),
            format_func=_label_row,
            key="cal_selected_rowid",
        )
        rowid = int(st.session_state["cal_selected_rowid"])

    # -------------------------
    # 3.2 ฟอร์มรายละเอียด (เหมือนหน้า “รายละเอียดครุภัณฑ์” แต่เป็นของแผนสอบเทียบ)
    # -------------------------
    if rowid is None or rowid not in df_raw.index:
        st.info("👆 เลือกรายการ 1 แถวจากตารางด้านบน เพื่อแสดงรายละเอียดสำหรับแก้ไข")
    else:
        r = df_raw.loc[rowid]

        def _sval(col):
            if col is None:
                return ""
            v = r.get(col)
            if pd.isna(v):
                return ""
            return str(v)

        # คอลัมน์รายเดือน 1-12
        month_cols = []
        for c in df_raw.columns:
            s = str(c).strip()
            if s.isdigit():
                m = int(s)
                if 1 <= m <= 12:
                    month_cols.append((m, c))
        month_cols.sort(key=lambda x: x[0])

        # คอลัมน์ที่เป็น boolean/flag ที่พบบ่อย
        cal_flag_col = _pick_col(["สอบเทียบ", "Calibration"])
        ver_flag_col = _pick_col(["ทวนสอบ", "Verification"])

        st.markdown(
            """
            <div class="mem-card">
              <div class="mem-page-title" style="margin:0;">รายละเอียดแผนสอบเทียบ</div>
              <div class="mem-page-subtitle" style="margin-top:0.25rem;">
                ฟอร์มรายละเอียด (แก้ไขข้อมูลแล้วกด <b>บันทึก</b> เพื่อเขียนกลับไฟล์ Excel)
              </div>
            """,
            unsafe_allow_html=True,
        )

        # เตรียมค่าวันที่
        cur_due_dt = pd.to_datetime(r.get(due_col), errors="coerce") if (due_col and due_col in df_raw.columns) else pd.NaT
        cur_last_dt = pd.to_datetime(r.get(last_col), errors="coerce") if (last_col and last_col in df_raw.columns) else pd.NaT

        # ฟิลด์หลักที่จะถือว่า "สำคัญ" และไม่ต้องซ้ำในข้อมูลเพิ่มเติม
        used_cols = set([c for c in [no_col, id_col, name_col, assetid_col, manu_col, model_col, sn_col, dept_col, vendor_col, last_col, due_col, note_col, cal_flag_col, ver_flag_col] if c])

        with st.form("cal_detail_form_full", clear_on_submit=False):
            st.markdown("### ฟอร์มรายละเอียด")

            # แถวที่ 1
            c1, c2 = st.columns(2)
            with c1:
                v_no = st.text_input("ลำดับ / No.", value=_sval(no_col), disabled=(no_col is None))
                v_id = st.text_input("รหัส / ID Code", value=_sval(id_col), disabled=(id_col is None))
                v_name = st.text_input("ชื่อเครื่องมือ / Equipment", value=_sval(name_col), disabled=(name_col is None))
                v_dept = st.text_input("หน่วยงาน / Department", value=_sval(dept_col), disabled=(dept_col is None))
            with c2:
                v_assetid = st.text_input("ทะเบียน / Asset ID", value=_sval(assetid_col), disabled=(assetid_col is None))
                v_manu = st.text_input("ยี่ห้อ/ผู้ผลิต / Manufacturer", value=_sval(manu_col), disabled=(manu_col is None))
                v_model = st.text_input("รุ่น / Model", value=_sval(model_col), disabled=(model_col is None))
                v_sn = st.text_input("S/N", value=_sval(sn_col), disabled=(sn_col is None))

            st.markdown("### ข้อมูลการสอบเทียบ")
            c3, c4 = st.columns(2)
            with c3:
                v_vendor = st.text_input("ผู้รับจ้าง/ผู้ให้บริการ / Vendor", value=_sval(vendor_col), disabled=(vendor_col is None))

                if last_col is None:
                    st.text_input("วันที่สอบเทียบล่าสุด (ไม่พบคอลัมน์)", value="", disabled=True)
                    v_last_clear = True
                    v_last_date = None
                else:
                    v_last_clear = st.checkbox(
                        "ล้างวันที่สอบเทียบล่าสุด (ให้เป็นค่าว่าง)",
                        value=pd.isna(cur_last_dt),
                        key=f"cal_last_clear_{rowid}",
                    )
                    v_last_date = st.date_input(
                        "วันที่สอบเทียบล่าสุด",
                        value=(None if pd.isna(cur_last_dt) else cur_last_dt.date()),
                        disabled=v_last_clear,
                        key=f"cal_last_date_{rowid}",
                    )
            with c4:
                # วันที่ครบกำหนด (Due)
                v_due_clear = st.checkbox(
                    "ล้างวันครบกำหนดสอบเทียบ (ให้เป็นค่าว่าง)",
                    value=pd.isna(cur_due_dt),
                    key=f"cal_due_clear_{rowid}",
                )
                v_due_date = st.date_input(
                    "วันครบกำหนดสอบเทียบ (Due Date)",
                    value=(None if pd.isna(cur_due_dt) else cur_due_dt.date()),
                    disabled=v_due_clear,
                    key=f"cal_due_date_{rowid}",
                )

                # flags
                if cal_flag_col is not None:
                    cur_flag = r.get(cal_flag_col)
                    v_cal_flag = st.checkbox("งานนี้เป็น “สอบเทียบ”", value=bool(cur_flag) and str(cur_flag).lower() not in ["nan", "none", "0", ""], key=f"cal_flag_{rowid}")
                else:
                    v_cal_flag = None
                if ver_flag_col is not None:
                    cur_flag = r.get(ver_flag_col)
                    v_ver_flag = st.checkbox("งานนี้เป็น “ทวนสอบ”", value=bool(cur_flag) and str(cur_flag).lower() not in ["nan", "none", "0", ""], key=f"ver_flag_{rowid}")
                else:
                    v_ver_flag = None

            v_note = st.text_area("หมายเหตุ / Note", value=_sval(note_col), height=110, disabled=(note_col is None))

            # แผนรายเดือน 1-12 (ถ้ามี)
            if month_cols:
                st.markdown("### แผนรายเดือน (1–12)")
                month_names = {
                    1:"ม.ค.",2:"ก.พ.",3:"มี.ค.",4:"เม.ย.",5:"พ.ค.",6:"มิ.ย.",
                    7:"ก.ค.",8:"ส.ค.",9:"ก.ย.",10:"ต.ค.",11:"พ.ย.",12:"ธ.ค."
                }
                # 6 ต่อแถว
                rows = [month_cols[i:i+6] for i in range(0, len(month_cols), 6)]
                month_state = {}
                for rr in rows:
                    cols = st.columns(len(rr))
                    for (mnum, ccol), cc in zip(rr, cols):
                        with cc:
                            cur_v = r.get(ccol)
                            checked = (not pd.isna(cur_v)) and (str(cur_v).strip() not in ["", "0", "None", "nan"])
                            month_state[ccol] = st.checkbox(month_names.get(mnum, str(mnum)), value=checked, key=f"m_{rowid}_{mnum}")
            else:
                month_state = {}

            # ข้อมูลเพิ่มเติม (คอลัมน์อื่น ๆ ทั้งหมด)
            with st.expander("ข้อมูลเพิ่มเติม (คอลัมน์อื่น ๆ ในไฟล์)", expanded=False):
                extra_cols = [c for c in df_raw.columns if c not in used_cols and (not str(c).strip().isdigit())]
                extra_inputs = {}
                for c in extra_cols:
                    v = r.get(c)
                    # ข้ามคอลัมน์ที่ระบบคำนวณเองถ้ามี
                    if str(c) in ["days_left", "สถานะกำหนด", "สถานะ"]:
                        st.text_input(str(c), value=("" if pd.isna(v) else str(v)), disabled=True)
                        continue
                    if pd.api.types.is_numeric_dtype(df_raw[c]):
                        try:
                            extra_inputs[c] = st.number_input(str(c), value=(0.0 if pd.isna(v) else float(v)))
                        except Exception:
                            extra_inputs[c] = st.text_input(str(c), value=("" if pd.isna(v) else str(v)))
                    else:
                        extra_inputs[c] = st.text_input(str(c), value=("" if pd.isna(v) else str(v)))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                do_save = st.form_submit_button("💾 บันทึกข้อมูลแผนสอบเทียบ", use_container_width=True)
            with col_btn2:
                do_cancel = st.form_submit_button("↩️ ไม่บันทึก", use_container_width=True)

        if do_save:
            # อัปเดตค่ากลับ df_raw
            if no_col is not None:
                df_raw.loc[rowid, no_col] = v_no
            if id_col is not None:
                df_raw.loc[rowid, id_col] = v_id
            if name_col is not None:
                df_raw.loc[rowid, name_col] = v_name
            if dept_col is not None:
                df_raw.loc[rowid, dept_col] = v_dept

            if assetid_col is not None:
                df_raw.loc[rowid, assetid_col] = v_assetid
            if manu_col is not None:
                df_raw.loc[rowid, manu_col] = v_manu
            if model_col is not None:
                df_raw.loc[rowid, model_col] = v_model
            if sn_col is not None:
                df_raw.loc[rowid, sn_col] = v_sn

            if vendor_col is not None:
                df_raw.loc[rowid, vendor_col] = v_vendor
            if note_col is not None:
                df_raw.loc[rowid, note_col] = v_note

            if last_col is not None:
                df_raw.loc[rowid, last_col] = (pd.NaT if v_last_clear else pd.to_datetime(v_last_date))
            if due_col is not None:
                df_raw.loc[rowid, due_col] = (pd.NaT if v_due_clear else pd.to_datetime(v_due_date))

            if cal_flag_col is not None and v_cal_flag is not None:
                df_raw.loc[rowid, cal_flag_col] = (1 if v_cal_flag else "")
            if ver_flag_col is not None and v_ver_flag is not None:
                df_raw.loc[rowid, ver_flag_col] = (1 if v_ver_flag else "")

            # แผนรายเดือน
            for ccol, checked in month_state.items():
                if checked:
                    cur_v = df_raw.loc[rowid, ccol]
                    if pd.isna(cur_v) or str(cur_v).strip() in ["", "0", "None", "nan"]:
                        df_raw.loc[rowid, ccol] = 1
                else:
                    df_raw.loc[rowid, ccol] = ""

            # ข้อมูลเพิ่มเติม
            try:
                for c, v in extra_inputs.items():
                    df_raw.loc[rowid, c] = v
            except Exception:
                pass

            save_calibration_plan(df_raw)
            st.success("✅ บันทึกข้อมูลแผนสอบเทียบเรียบร้อย")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("🛠️ โหมดขั้นสูง: แก้ไขทั้งตาราง (เหมือนเดิม)", expanded=False):
        editable_cols = [c for c in df_raw.columns]
        edited_df = st.data_editor(
            df_raw[editable_cols],
            key="cal_plan_editor",
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )

        if st.button("💾 บันทึกแผนสอบเทียบทั้งหมด", use_container_width=True, key="cal_save_all"):
            save_calibration_plan(edited_df)
            st.rerun()

# ====================================================================
# หน้า "รายงานสรุป" – admin
# ====================================================================
def page_summary():
    set_main_style()
    role = st.session_state.get("role", "user")
    if role != "admin":
        st.warning("หน้านี้สำหรับผู้ดูแลระบบเท่านั้น")
        return

    st.markdown(
        '<div class="mem-page-title">รายงานสรุป</div>',
        unsafe_allow_html=True,
    )
    st.info("ส่วนนี้ใช้ทำรายงานสรุปครุภัณฑ์ / วิเคราะห์ข้อมูลเพิ่มเติมในอนาคต")

# ====================================================================
# Main app (หลัง login)
# ====================================================================
def main_app():
    set_main_style()

    username = st.session_state.get("username", "")
    display_name = st.session_state.get("display_name", username or "ผู้ใช้")
    role = st.session_state.get("role", "user")
    role_label = "ผู้ดูแลระบบ" if role == "admin" else "ผู้ใช้ทั่วไป"

    avatar_text = (display_name[:2] or "ME").upper()

    with st.sidebar:
        st.markdown(
            f"""
            <div class="mem-sidebar-user">
              <div style="font-size:28px; font-weight:700; margin-bottom:4px;">{avatar_text}</div>
              <div class="mem-sidebar-user-name">{display_name}</div>
              <div class="mem-sidebar-user-sub">{role_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Badge สถานะแจ้งซ่อมแบบ real-time สำหรับ admin
        if role == "admin":
            df_sidebar = load_equipment_data()
            open_count = 0
            new_today_count = 0
            if not df_sidebar.empty and "สถานะแจ้งซ่อม" in df_sidebar.columns:
                open_mask = (
                    df_sidebar["สถานะแจ้งซ่อม"].astype(str)
                    == "แจ้งซ่อมแล้ว - กำลังดำเนินการ"
                )
                open_count = int(open_mask.sum())
                if MAINT_REQUEST_DATE_COL in df_sidebar.columns:
                    dates = pd.to_datetime(
                        df_sidebar.loc[open_mask, MAINT_REQUEST_DATE_COL],
                        errors="coerce",
                    )
                    today = pd.to_datetime(pd.Timestamp.today().normalize()).date()
                    new_today_count = int((dates.dt.date == today).sum())
            st.markdown(
                f"""
                <div style="margin-top:8px;margin-bottom:12px;">
                  <div style="font-size:12px;color:#9CA3AF;margin-bottom:4px;">สถานะแจ้งซ่อม</div>
                  <div style="display:flex;gap:6px;flex-wrap:wrap;">
                    <div style="background:#111827;border-radius:999px;padding:3px 10px;font-size:11px;color:#F9FAFB;">
                      เปิดอยู่: {open_count}
                    </div>
                    <div style="background:#F97316;border-radius:999px;padding:3px 10px;font-size:11px;color:#111827;">
                      ใหม่วันนี้: {new_today_count}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<div class="mem-menu-title">เมนู</div>', unsafe_allow_html=True)

        current_menu = st.session_state.get("current_menu", "หน้าหลัก")

        if role == "admin":
            menu_labels = [
                "หน้าหลัก",
                "รายการครุภัณฑ์",
                "แจ้งซ่อม / บำรุงรักษา",
                "แผนสอบเทียบ",
                "รายงานสรุป",
            ]
        else:
            menu_labels = ["รายการครุภัณฑ์"]

        if current_menu not in menu_labels:
            current_menu = menu_labels[0]
            st.session_state.current_menu = current_menu

        def menu_button(label: str):
            is_active = current_menu == label
            css_class = "mem-menu-btn-active" if is_active else "mem-menu-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            clicked = st.button(label, use_container_width=True, key=f"menu_{label}")
            st.markdown("</div>", unsafe_allow_html=True)
            return clicked

        for label in menu_labels:
            if menu_button(label):
                st.session_state.current_menu = label
                st.rerun()

        st.write("")
        if st.button("Logout", type="primary", use_container_width=True):
            # 🔒===============================
            #  ตอน logout เคลียร์ query params เสมอ
            #  เพื่อไม่ให้ F5 แล้ว restore login
            # ===============================#
            try:
                st.experimental_set_query_params()
            except Exception:
                pass
            # ================================

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

# ====================================================================
# ENTRY POINT + F5 / QR restore login
# ====================================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "view" not in st.session_state:
    st.session_state.view = "landing"
if "current_menu" not in st.session_state:
    st.session_state.current_menu = "หน้าหลัก"
if "selected_row_idx" not in st.session_state:
    st.session_state.selected_row_idx = 0
if "qr_code_from_url" not in st.session_state:
    st.session_state.qr_code_from_url = None
if "qr_code_pending" not in st.session_state:
    st.session_state.qr_code_pending = None
if "_url_params" not in st.session_state:
    st.session_state._url_params = {}

# ---- อ่าน query parameter หนึ่งครั้ง (ใช้ทั้งกัน F5 + QR) ----
try:
    params = st.experimental_get_query_params()
except Exception:
    params = {}

st.session_state._url_params = params

username_from_url = None
if isinstance(params, dict) and "user" in params:
    v = params["user"]
    if isinstance(v, list):
        username_from_url = v[0]
    else:
        username_from_url = v

code_from_url = None
if isinstance(params, dict) and "code" in params:
    cv = params["code"]
    if isinstance(cv, list):
        code_from_url = cv[0]
    else:
        code_from_url = cv

if code_from_url:
    st.session_state.qr_code_from_url = str(code_from_url)

# 🔒========================================================
#  Restore login จาก query parameter (กัน F5 / Refresh หลุด)
#  ถ้ามี ?user=xxx อยู่ใน URL → ดึงข้อมูล user จาก auth แล้วเซ็ต session_state
# ========================================================#
if not st.session_state.logged_in and username_from_url:
    display_name = get_user_display_name(username_from_url)
    if display_name:
        st.session_state.logged_in = True
        st.session_state.username = username_from_url
        st.session_state.display_name = display_name
        role = get_user_role(username_from_url) or "user"
        st.session_state.role = role
        if "current_menu" not in st.session_state or st.session_state.get("current_menu") is None:
            st.session_state.current_menu = (
                "หน้าหลัก" if role == "admin" else "รายการครุภัณฑ์"
            )
        # ถ้ามี code อยู่ใน URL ให้ไปหน้ารายการครุภัณฑ์โดยตรง
        if st.session_state.get("qr_code_from_url"):
            st.session_state.current_menu = "รายการครุภัณฑ์"
        st.session_state.view = "app"
# ========================================================#

# ---- ถ้ายังไม่ล็อกอิน และมี code ใน URL และยังไม่ได้กดไปหน้า login/register → โชว์หน้า QR public ----
if (
    not st.session_state.logged_in
    and code_from_url
    and st.session_state.view not in ("login", "register")
):
    st.session_state.view = "qr_public"

# ---- routing หลัก ----
if st.session_state.logged_in:
    main_app()
else:
    if st.session_state.view == "login":
        login_page()
    elif st.session_state.view == "register":
        register_page()
    elif st.session_state.view == "qr_public":
        qr_public_page()
    else:
        landing_page()
