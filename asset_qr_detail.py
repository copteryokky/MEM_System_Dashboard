# asset_qr_detail.py
import pandas as pd
import streamlit as st
from pathlib import Path
from urllib.parse import quote_plus

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# -----------------------------
# CONFIG หน้า QR Detail
# -----------------------------
st.set_page_config(
    page_title="รายละเอียดครุภัณฑ์ (QR)",
    page_icon="🔧",
    layout="wide",
)

EXCEL_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"  # ใช้เป็นรหัสใน QR
EXCEL_PATH_FALLBACK = DEFAULT_EXCEL_PATH


# -----------------------------
# Helper: Excel
# -----------------------------
def get_current_excel_path() -> Path | None:
    """
    ใช้กฎเดียวกับ MEM System:
    - ใช้ DEFAULT_EXCEL_NAME ถ้ามี
    - ถ้าไม่มีให้ใช้ไฟล์แรกใน data/*.xls*
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ถ้ามีไฟล์ default ที่ config ชี้ไว้
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    # ไม่มีก็ลองหาไฟล์อื่นในโฟลเดอร์ data
    files = sorted(DATA_DIR.glob("*.xls*"))
    if files:
        return files[0]

    return None


def load_equipment_data() -> pd.DataFrame:
    path = get_current_excel_path()
    if path is None or not path.exists():
        st.error("ไม่พบไฟล์ Excel สำหรับเก็บข้อมูลครุภัณฑ์")
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def save_equipment_data(df: pd.DataFrame):
    path = get_current_excel_path()
    if path is None:
        st.error("ยังไม่ได้กำหนดไฟล์ Excel ที่จะบันทึก")
        return

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_excel(path, index=False)
        st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")


# -----------------------------
# UI Helper
# -----------------------------
def nice_title(text: str):
    st.markdown(
        f"""
        <div style="font-size:26px;font-weight:700;margin-bottom:0.3rem;color:#111827;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sub_title(text: str):
    st.markdown(
        f"""
        <div style="font-size:13px;color:#6B7280;margin-bottom:1.0rem;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# READ PARAM FROM URL
# -----------------------------
params = st.experimental_get_query_params()
code_from_qr = params.get("code", [""])[0].strip()

nice_title("ข้อมูลเครื่องมือห้องปฏิบัติการ")
sub_title(
    "หน้านี้ใช้สำหรับแสดงและแก้ไขรายละเอียดครุภัณฑ์จากการสแกน QR Code "
    f"(อ้างอิงจากคอลัมน์ <b>{EXCEL_CODE_COL}</b> ในไฟล์ Excel)",
)

df = load_equipment_data()
if df.empty:
    st.stop()

if EXCEL_CODE_COL not in df.columns:
    st.error(f"ไม่พบคอลัมน์ '{EXCEL_CODE_COL}' ในไฟล์ Excel")
    st.stop()

# -----------------------------
# เลือกแถวจาก code
# -----------------------------
if code_from_qr:
    # กรณีเข้าจาก QR
    mask = df[EXCEL_CODE_COL].astype(str).str.strip() == code_from_qr
    matches = df[mask]
    if matches.empty:
        st.error(
            f"ไม่พบครุภัณฑ์ที่มี '{EXCEL_CODE_COL}' = {code_from_qr} "
            "กรุณาตรวจสอบรหัสหรือไฟล์ Excel"
        )
        st.stop()
    row_idx = matches.index[0]
else:
    # กรณีเปิดหน้าเอง ยังไม่มี code -> เลือกจาก dropdown
    st.warning("ไม่ได้ระบุ code ใน URL (ตัวอย่าง: ?code=LAB-AS-001) เลือกจากรายการด้านล่างได้")
    codes = (
        df[EXCEL_CODE_COL]
        .astype(str)
        .fillna("")
        .str.strip()
        .replace("nan", "")
    )
    options = [
        f"{i+1:03d} - {codes.iloc[i]}"
        for i in range(len(codes))
    ]
    selected = st.selectbox("เลือกครุภัณฑ์จากรหัสเครื่องมือห้องปฏิบัติการ", options)
    row_idx = int(selected.split(" - ")[0]) - 1
    code_from_qr = codes.iloc[row_idx]

row_data = df.iloc[row_idx].to_dict()

asset_name = str(row_data.get("ชื่อ", row_data.get("ชื่อครุภัณฑ์", "")))
asset_code = str(row_data.get(EXCEL_CODE_COL, ""))

# -----------------------------
# Header Card (โชว์ code ใต้ QR)
# -----------------------------
left, right = st.columns([1, 2])

with left:
    st.markdown(
        """
        <div style="
            background:#111827;
            border-radius:20px;
            padding:18px 16px;
            color:#E5E7EB;
            box-shadow:0 18px 40px rgba(15,23,42,0.6);
            text-align:center;
            ">
            <div style="font-size:13px;opacity:0.85;">รหัสเครื่องมือห้องปฏิบัติการ</div>
            <div style="font-size:20px;font-weight:700;margin-top:4px;color:#f97316;">
        """
        + asset_code
        + """
            </div>
            <div style="font-size:11px;margin-top:6px;color:#9CA3AF;">
                (รหัสนี้ถูกใช้ฝังอยู่ใน QR Code)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        f"""
        <div style="
            background:#FFFFFF;
            border-radius:20px;
            padding:16px 18px;
            box-shadow:0 10px 25px rgba(15,23,42,0.08);
            border:1px solid #E5E7EB;
        ">
            <div style="font-size:13px;color:#6B7280;margin-bottom:4px;">ชื่อครุภัณฑ์</div>
            <div style="font-size:18px;font-weight:600;color:#111827;">
                {asset_name if asset_name else "(ไม่ระบุชื่อ)"}
            </div>
            <div style="font-size:11px;color:#9CA3AF;margin-top:6px;">
                สามารถแก้ไขข้อมูลในฟอร์มด้านล่าง แล้วกด "บันทึกข้อมูล" เพื่ออัปเดตไฟล์ Excel ได้ทันที
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# -----------------------------
# ฟอร์มรายละเอียด (2 คอลัมน์)
# -----------------------------
st.markdown(
    "<div style='font-size:18px;font-weight:700;margin-bottom:0.4rem;'>ฟอร์มรายละเอียดครุภัณฑ์</div>",
    unsafe_allow_html=True,
)

columns_list = list(df.columns)
half = (len(columns_list) + 1) // 2
left_cols = columns_list[:half]
right_cols = columns_list[half:]

with st.form("asset_detail_form"):
    c1, c2 = st.columns(2)
    updated_values: dict[str, str] = {}

    # ฟังก์ชันเลือก widget แบบ text_input / text_area ตามชื่อคอลัมน์
    def field_widget(col_name: str, value: str, key: str) -> str:
        lower = col_name.lower()
        if any(k in lower for k in ["หมายเหตุ", "รายละเอียด", "description", "note"]):
            return st.text_area(col_name, value=value, key=key)
        else:
            return st.text_input(col_name, value=value, key=key)

    with c1:
        for col in left_cols:
            current_val = row_data.get(col, "")
            val_str = "" if pd.isna(current_val) else str(current_val)
            updated_values[col] = field_widget(
                col, val_str, key=f"left_{col}_{row_idx}"
            )

    with c2:
        for col in right_cols:
            current_val = row_data.get(col, "")
            val_str = "" if pd.isna(current_val) else str(current_val)
            updated_values[col] = field_widget(
                col, val_str, key=f"right_{col}_{row_idx}"
            )

    submitted = st.form_submit_button("บันทึกข้อมูล", type="primary")

if submitted:
    # เขียนค่ากลับเข้า df (เก็บเป็น string ทั้งหมด ง่ายและปลอดภัย)
    for col in columns_list:
        df.at[row_idx, col] = updated_values.get(col, "")

    save_equipment_data(df)
    st.experimental_set_query_params(code=code_from_qr)
    st.experimental_rerun()
