# asset_qr_detail.py
import pandas as pd
import streamlit as st
from pathlib import Path
from urllib.parse import quote_plus
from io import BytesIO

import qrcode
from PIL import Image

from config import DATA_DIR, DEFAULT_EXCEL_PATH

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="รายละเอียดครุภัณฑ์ (QR)",
    page_icon="🔧",
    layout="wide",
)

EXCEL_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"
EXCEL_NAME_COL = "ชื่อ"

# ให้ตรงกับตอนสร้าง QR จริง
QR_BASE_URL = "https://mem-system-dashboard.streamlit.app"  # <-- แก้ให้ตรงของคุณ
QR_PAGE_PATH = ""  # ถ้าใช้ root ให้เว้นว่าง "", ถ้าใช้ /asset ให้ใส่ "/asset"


# =========================
# Helper: Excel
# =========================
def get_excel_path() -> Path | None:
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    files = sorted(Path(DATA_DIR).glob("*.xls*"))
    return files[0] if files else None


def load_df() -> pd.DataFrame:
    path = get_excel_path()
    if not path or not path.exists():
        st.error("ไม่พบไฟล์ Excel สำหรับข้อมูลครุภัณฑ์")
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def save_df(df: pd.DataFrame):
    path = get_excel_path()
    if not path:
        st.error("ยังไม่ได้ตั้งค่าไฟล์ Excel ใน config.py")
        return

    try:
        df.to_excel(path, index=False)
        st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")


# =========================
# Helper: QR
# =========================
def make_qr_buffer(url: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# =========================
# MAIN PAGE
# =========================
st.title("ข้อมูลเครื่องมือห้องปฏิบัติการ")

df = load_df()
if df.empty:
    st.stop()

if EXCEL_CODE_COL not in df.columns:
    st.error(f"ไม่พบคอลัมน์ '{EXCEL_CODE_COL}' ในไฟล์ Excel")
    st.stop()

# ---------- อ่าน code จาก URL (ใช้ st.query_params แทน experimental_get) ----------
q = st.query_params
code_from_url = ""
if "code" in q:
    # st.query_params คืน list หรือ str ขึ้นกับเวอร์ชัน
    val = q["code"]
    if isinstance(val, list):
        code_from_url = val[0]
    else:
        code_from_url = val

# หา index จาก code
selected_index = 0
if code_from_url:
    matches = df.index[df[EXCEL_CODE_COL].astype(str) == str(code_from_url)].tolist()
    if matches:
        selected_index = matches[0]

# ---------- แถบแจ้งเตือนด้านบน ----------
if not code_from_url:
    st.info(
        "ไม่ได้รับค่า code ใน URL (ตัวอย่าง: ?code=LAB-AS-001) "
        "คุณสามารถเลือกจากรายการด้านล่างได้"
    )

# ---------- เลือกครุภัณฑ์ ----------
def format_option(i: int) -> str:
    row = df.iloc[i]
    name = str(row.get(EXCEL_NAME_COL, "ไม่ทราบชื่อ"))
    code = str(row.get(EXCEL_CODE_COL, ""))
    return f"{i+1:03d} - {name} ({code})"


options_index = list(df.index)
selected_index = st.selectbox(
    "เลือกครุภัณฑ์จากรหัสเครื่องมือห้องปฏิบัติการ",
    options=options_index,
    index=selected_index,
    format_func=format_option,
)

current_row = df.iloc[selected_index].copy()
current_code = str(current_row.get(EXCEL_CODE_COL, "")).strip()
current_name = str(current_row.get(EXCEL_NAME_COL, "")).strip()

# ถ้าเลือกต่างจาก code เดิม ให้ set query params ใหม่ (ใช้ API ใหม่)
if current_code and current_code != code_from_url:
    st.query_params = {"code": current_code}

# ---------- การ์ดหัวข้อ ----------
st.markdown(
    f"""
    <div style="
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        padding: 18px 22px;
        border-radius: 20px;
        background: #0f172a;
        color: #f9fafb;
        box-shadow: 0 16px 40px rgba(15,23,42,0.6);
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <div style="font-size:14px;">
            <div style="font-size:12px;opacity:0.8;">รหัสเครื่องมือห้องปฏิบัติการ</div>
            <div style="font-size:22px;font-weight:700;">{current_code or '-'} </div>
            <div style="font-size:11px;opacity:0.6;">(รหัสที่ถูกใช้พิมพ์ใน QR Code)</div>
        </div>
        <div style="font-size:13px;max-width:60%; text-align:right;">
            <div style="font-size:12px;opacity:0.8;">ชื่อครุภัณฑ์</div>
            <div style="font-size:16px;font-weight:600;">{current_name or '-'}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### ฟอร์มรายละเอียด")

# ---------- ฟอร์มรายละเอียด 2 คอลัมน์ ----------
columns_list = list(df.columns)
half = (len(columns_list) + 1) // 2
left_cols = columns_list[:half]
right_cols = columns_list[half:]

col_left, col_right = st.columns(2)
updated_values = {}

with col_left:
    for col in left_cols:
        val = current_row.get(col, "")
        val_str = "" if pd.isna(val) else str(val)
        updated_values[col] = st.text_input(
            str(col), value=val_str, key=f"left_{col}_{selected_index}"
        )

with col_right:
    for col in right_cols:
        val = current_row.get(col, "")
        val_str = "" if pd.isna(val) else str(val)
        updated_values[col] = st.text_input(
            str(col), value=val_str, key=f"right_{col}_{selected_index}"
        )

# ---------- แสดง QR ในกรอบด้านล่าง (ตำแหน่งที่คุณวงสีแดง) ----------
st.markdown("---")

qr_col1, qr_col2 = st.columns([2, 1])

with qr_col1:
    # ปุ่มบันทึกอยู่ฝั่งซ้ายเหมือนเดิม
    if st.button("บันทึกการแก้ไข", type="primary"):
        df_current = load_df()
        if df_current.empty:
            st.stop()

        # อัปเดตค่าตามฟอร์ม
        for col in columns_list:
            raw_val = updated_values.get(col, "")
            orig_dtype = df_current[col].dtype if col in df_current.columns else object

            if pd.api.types.is_numeric_dtype(orig_dtype):
                if raw_val == "":
                    df_current.at[selected_index, col] = pd.NA
                else:
                    try:
                        df_current.at[selected_index, col] = pd.to_numeric(raw_val)
                    except Exception:
                        df_current.at[selected_index, col] = raw_val
            else:
                df_current.at[selected_index, col] = raw_val

        save_df(df_current)
        st.rerun()

with qr_col2:
    st.markdown("#### QR Code ของรายการนี้")
    if current_code:
        encoded_code = quote_plus(current_code)
        qr_url = f"{QR_BASE_URL}{QR_PAGE_PATH}?code={encoded_code}"
        buf = make_qr_buffer(qr_url)
        st.image(
            buf,
            caption=f"รหัส: {current_code}",
            width=260,
        )
        st.caption(qr_url)
    else:
        st.info("ไม่มีรหัสเครื่องมือห้องปฏิบัติการสำหรับสร้าง QR")
