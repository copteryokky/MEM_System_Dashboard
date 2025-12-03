# asset_qr_detail.py
# หน้าแสดง / แก้ไขข้อมูลครุภัณฑ์จากการสแกน QR
# ใช้ไฟล์ Excel เดียวกับระบบหลัก (กำหนดจาก config.py)

import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# =========================
# CONFIG พื้นฐาน
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
    page_title="ข้อมูลครุภัณฑ์จาก QR",
    page_icon="🔎",
    layout="wide",
)

# =========================
# Helper: Excel
# =========================
def get_excel_path() -> Path | None:
    """
    เลือกไฟล์ Excel ที่ใช้เป็นฐานข้อมูล
    - ถ้ามี DEFAULT_EXCEL_PATH ให้ใช้ไฟล์นั้นก่อน
    - ถ้าไม่มี ให้ใช้ไฟล์แรกในโฟลเดอร์ data
    """
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.xls*"))
    if not files:
        return None

    for f in files:
        if f.name == DEFAULT_EXCEL_NAME:
            return f
    return files[0]


def load_equipment_data(path: Path) -> pd.DataFrame:
    """อ่านข้อมูลครุภัณฑ์จาก Excel ให้แน่ใจว่ามีคอลัมน์ที่จำเป็น"""
    try:
        df = pd.read_excel(path).dropna(how="all").reset_index(drop=True)

        if "สถานะแจ้งซ่อม" not in df.columns:
            df["สถานะแจ้งซ่อม"] = MAINT_STATUS_CHOICES[0]
        if "รูปภาพครุภัณฑ์" not in df.columns:
            df["รูปภาพครุภัณฑ์"] = ""

        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def save_equipment_data(df: pd.DataFrame, path: Path):
    """บันทึก DataFrame กลับลงไฟล์ Excel"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_excel(path, index=False)
        st.success(
            f"บันทึกการแก้ไขเรียบร้อยแล้ว (ทั้งหน้า QR และหน้าแอดมินจะเห็นข้อมูลเหมือนกัน)"
        )
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")

# =========================
# Helper: รูปภาพ & QR
# =========================
def get_image_path_from_row(row: pd.Series) -> Path | None:
    """อ่าน path รูปจากคอลัมน์ 'รูปภาพครุภัณฑ์' แล้วแปลงเป็น Path จริง"""
    val = str(row.get("รูปภาพครุภัณฑ์", "") or "").strip()
    if not val:
        return None
    p = Path(val)
    if not p.is_absolute():
        p = IMAGE_DIR / p.name
    return p


def save_uploaded_image(uploaded, asset_code: str) -> str:
    """บันทึกรูปที่อัปโหลดลงโฟลเดอร์ asset_images แล้วคืนชื่อไฟล์"""
    suffix = Path(uploaded.name).suffix or ".png"
    safe_code = asset_code.replace("/", "_").replace("\\", "_").replace(" ", "_")
    filename = f"{safe_code}{suffix}"
    target_path = IMAGE_DIR / filename
    with open(target_path, "wb") as f:
        f.write(uploaded.getbuffer())
    return filename


def generate_qr_bytes(url: str) -> bytes:
    """สร้างรูป QR เป็น bytes เพื่อเอาไปแสดง / ดาวน์โหลด"""
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

# =========================
# อ่าน query param จาก URL
# =========================
try:
    query_params = st.query_params  # streamlit รุ่นใหม่
except Exception:
    query_params = st.experimental_get_query_params()  # เผื่อรันบนรุ่นเก่า

if isinstance(query_params, dict):
    asset_code = query_params.get("code", [""])[0].strip()
else:
    asset_code = ""

if not asset_code:
    st.error("ไม่พบรหัสครุภัณฑ์จาก QR (parameter `code` ว่าง)")
    st.stop()

# =========================
# โหลดข้อมูลจาก Excel
# =========================
excel_path = get_excel_path()
if not excel_path or not excel_path.exists():
    st.error("ไม่พบไฟล์ Excel ฐานข้อมูลครุภัณฑ์ (ตรวจโฟลเดอร์ data และ config.py)")
    st.stop()

df = load_equipment_data(excel_path)
if df.empty or ASSET_CODE_COL not in df.columns:
    st.error(
        "ไม่พบข้อมูลครุภัณฑ์ หรือไม่มีคอลัมน์รหัสเครื่องมือห้องปฏิบัติการในไฟล์ Excel"
    )
    st.stop()

row_df = df[df[ASSET_CODE_COL].astype(str) == asset_code]
if row_df.empty:
    st.error(f"ไม่พบครุภัณฑ์ที่มีรหัส: {asset_code}")
    st.stop()

row = row_df.iloc[0]
row_index = row_df.index[0]

# =========================
# ส่วนหัวหน้าเว็บ
# =========================
name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))
st.title(f"รหัสครุภัณฑ์: {asset_code}")
st.subheader(f"ชื่อครุภัณฑ์: {name}")

st.caption(
    f"ดึงข้อมูลจากไฟล์ Excel: **{excel_path.name}** (เก็บอยู่ในโฟลเดอร์ `data/` ของระบบหลัก)"
)
st.write("---")

# =========================
# แสดง QR + ข้อมูลสรุป
# =========================
col_qr, col_info = st.columns([1, 1.2])

with col_qr:
    st.markdown("### QR Code ของครุภัณฑ์")

    # URL ของหน้านี้เอง (เปลี่ยนเป็นโดเมนของแอป QR ของคุณได้)
    base_url = "https://memsystemdashboard-qr.streamlit.app"
    url_self = f"{base_url}/?code={asset_code}"

    qr_bytes = generate_qr_bytes(url_self)
    st.image(qr_bytes, use_column_width=True)
    st.caption(asset_code)

    st.download_button(
        "⬇️ ดาวน์โหลด QR (PNG)",
        data=qr_bytes,
        file_name=f"{asset_code}_qr.png",
        mime="image/png",
        use_container_width=True,
    )

    st.info(
        "สแกน QR นี้จากอุปกรณ์อื่น ๆ เพื่อเปิดหน้าข้อมูลครุภัณฑ์ และสามารถแก้ไขข้อมูลได้เหมือนกัน"
    )

with col_info:
    st.markdown("### ข้อมูลสรุปครุภัณฑ์")
    cols_left = [
        "ชื่อ",
        "รุ่น",
        "หมายเลขเครื่อง",
        "AssetID",
        "สถานะ",
        "สถานะแจ้งซ่อม",
    ]
    cols_right = [
        "ต้นทุนต่อหน่วย",
        "ประเภทครุภัณฑ์",
        "หมวดครุภัณฑ์",
        "สถานที่ใช้งาน (ปัจจุบัน)",
    ]

    c1, c2 = st.columns(2)
    with c1:
        for col in cols_left:
            if col in row.index:
                st.write(f"**{col}** : {row.get(col, '-')}")
    with c2:
        for col in cols_right:
            if col in row.index:
                st.write(f"**{col}** : {row.get(col, '-')}")

st.write("---")

# =========================
# ฟอร์มแก้ไขรายละเอียด
# =========================
st.markdown("## แก้ไขรายละเอียดครุภัณฑ์")

# ไม่รวมคอลัมน์พิเศษบางตัว
excluded_cols = {
    "รูปภาพครุภัณฑ์",
    "สถานะแจ้งซ่อม",
}
editable_cols = [c for c in df.columns if c not in excluded_cols]

half = (len(editable_cols) + 1) // 2
left_cols = editable_cols[:half]
right_cols = editable_cols[half:]

updated_values: dict[str, str] = {}

col_l, col_r = st.columns(2)

with col_l:
    for col_name in left_cols:
        current_val = row.get(col_name, "")
        new_val = st.text_input(
            str(col_name),
            value="" if pd.isna(current_val) else str(current_val),
            key=f"qr_left_{col_name}",
        )
        updated_values[col_name] = new_val

with col_r:
    for col_name in right_cols:
        current_val = row.get(col_name, "")
        new_val = st.text_input(
            str(col_name),
            value="" if pd.isna(current_val) else str(current_val),
            key=f"qr_right_{col_name}",
        )
        updated_values[col_name] = new_val

# =========================
# สถานะแจ้งซ่อม
# =========================
st.markdown("## สถานะแจ้งซ่อม")

current_maint = str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or "")
if current_maint not in MAINT_STATUS_CHOICES:
    current_maint = MAINT_STATUS_CHOICES[0]

maint_select = st.selectbox(
    "สถานะแจ้งซ่อม",
    MAINT_STATUS_CHOICES,
    index=MAINT_STATUS_CHOICES.index(current_maint),
    key="qr_maint_status",
)
updated_values["สถานะแจ้งซ่อม"] = maint_select

# =========================
# รูปภาพครุภัณฑ์
# =========================
st.markdown("## รูปภาพครุภัณฑ์")

current_img_path = get_image_path_from_row(row)
if current_img_path and current_img_path.exists():
    st.image(str(current_img_path), caption="รูปภาพปัจจุบัน", use_column_width=True)
else:
    st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")

uploaded_img = st.file_uploader(
    "อัปโหลดรูปภาพใหม่ (ถ้าไม่เลือก ระบบจะใช้รูปเดิม)",
    type=["png", "jpg", "jpeg"],
    key="qr_upload_image",
)

# =========================
# ปุ่มบันทึก
# =========================
st.write("")
if st.button("บันทึกการแก้ไข", type="primary", use_container_width=True):
    # โหลดข้อมูลล่าสุดอีกครั้งกันกรณีมีคนอื่นแก้พร้อมกัน
    df_current = load_equipment_data(excel_path)

    # หา index ของแถวนี้อีกครั้งจากรหัสครุภัณฑ์
    mask = df_current[ASSET_CODE_COL].astype(str) == asset_code
    idx_list = df_current.index[mask].tolist()
    if not idx_list:
        st.error("ไม่พบแถวข้อมูลนี้ในไฟล์ Excel แล้ว กรุณารีเฟรชหน้าหลัก")
    else:
        idx = idx_list[0]

        # อัปเดตค่าตาม updated_values
        for col in updated_values:
            if col not in df_current.columns:
                continue
            raw_val = updated_values.get(col, "")
            orig_dtype = df_current[col].dtype

            if pd.api.types.is_numeric_dtype(orig_dtype):
                if raw_val == "":
                    df_current.at[idx, col] = pd.NA
                else:
                    try:
                        df_current.at[idx, col] = pd.to_numeric(raw_val)
                    except Exception:
                        df_current.at[idx, col] = raw_val
            else:
                df_current.at[idx, col] = raw_val

        # ถ้าอัปโหลดรูปใหม่ ให้บันทึกไฟล์และเขียนชื่อไฟล์ลงคอลัมน์ "รูปภาพครุภัณฑ์"
        if uploaded_img is not None:
            filename = save_uploaded_image(uploaded_img, asset_code)
            if "รูปภาพครุภัณฑ์" not in df_current.columns:
                df_current["รูปภาพครุภัณฑ์"] = ""
            df_current.at[idx, "รูปภาพครุภัณฑ์"] = filename

        # เซฟลง Excel
        save_equipment_data(df_current, excel_path)

        # รีโหลดหน้าใหม่จากข้อมูลล่าสุด
        st.rerun()  # ✅ ใช้ st.rerun แทน st.experimental_rerun
