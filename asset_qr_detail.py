# asset_qr_public.py
import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode
from typing import Optional

from config import get_excel_path, DATA_DIR

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


def load_equipment_data() -> pd.DataFrame:
    path = get_excel_path()          # ✅ ใช้ Excel เดียวกับ app.py
    if not path.exists():
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
    path = get_excel_path()
    try:
        df.to_excel(path, index=False)
        st.success("บันทึกการแก้ไขเรียบร้อยแล้ว (ทั้งหน้า QR และหน้าแอดมินจะเห็นข้อมูลเหมือนกัน)")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")


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


def generate_qr_bytes(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ============ อ่าน code จาก URL ============
try:
    query_params = st.query_params
except Exception:
    query_params = st.experimental_get_query_params()

if isinstance(query_params, dict):
    asset_code = query_params.get("code", [""])[0].strip()
else:
    asset_code = ""

if not asset_code:
    st.error("ไม่พบรหัสครุภัณฑ์จาก QR (parameter `code` ว่าง)")
    st.stop()

df = load_equipment_data()
if df.empty or ASSET_CODE_COL not in df.columns:
    st.error("ไม่พบข้อมูลครุภัณฑ์ หรือไม่มีคอลัมน์รหัสเครื่องมือห้องปฏิบัติการในไฟล์ Excel")
    st.stop()

row_df = df[df[ASSET_CODE_COL].astype(str) == asset_code]
if row_df.empty:
    st.error(f"ไม่พบครุภัณฑ์ที่มีรหัส: {asset_code}")
    st.stop()

row = row_df.iloc[0]

# ============ UI ============
name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))
st.title(f"รหัสครุภัณฑ์: {asset_code}")
st.subheader(f"ชื่อครุภัณฑ์: {name}")
st.write("---")

col_qr, col_info = st.columns([1, 1.2])
with col_qr:
    st.markdown("### QR Code ของครุภัณฑ์")
    url_self = f"https://mem-system-dashboard-qr.streamlit.app/?code={asset_code}"
    qr_bytes = generate_qr_bytes(url_self)
    st.image(qr_bytes, use_column_width=True)
    st.download_button(
        "⬇️ ดาวน์โหลด QR (PNG)",
        data=qr_bytes,
        file_name=f"{asset_code}_qr.png",
        mime="image/png",
        use_container_width=True,
    )
    st.caption("สแกน QR นี้เพื่อเปิดหน้าข้อมูลครุภัณฑ์จากอุปกรณ์อื่น ๆ ได้เช่นกัน")

with col_info:
    st.markdown("### ข้อมูลสรุปครุภัณฑ์")
    # (เลือกฟิลด์ที่ต้องการแสดงเหมือนโค้ดเดิมของคุณได้)

st.write("---")
st.markdown("## แก้ไขข้อมูลจากหน้างาน")

current_maint = str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or "")
if current_maint not in MAINT_STATUS_CHOICES:
    current_maint = MAINT_STATUS_CHOICES[0]

maint_status = st.selectbox(
    "สถานะแจ้งซ่อม",
    MAINT_STATUS_CHOICES,
    index=MAINT_STATUS_CHOICES.index(current_maint),
)

current_note = str(row.get("บันทึกจากหน้างานล่าสุด", "") or "")
note = st.text_area(
    "บันทึกจากหน้างาน (เช่น อาการเสีย / สิ่งที่ตรวจพบ)",
    value=current_note,
    height=100,
)

st.markdown("### รูปภาพครุภัณฑ์")
img_path = get_image_path_from_row(row)
if img_path and img_path.exists():
    st.image(str(img_path), caption="รูปภาพปัจจุบัน", use_column_width=True)
else:
    st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")

uploaded_img = st.file_uploader(
    "อัปโหลดรูปภาพใหม่ (PNG / JPG / JPEG)",
    type=["png", "jpg", "jpeg"],
)

st.write("")
if st.button("บันทึกการแก้ไข", type="primary", use_container_width=True):
    df_current = load_equipment_data()

    mask = df_current[ASSET_CODE_COL].astype(str) == asset_code
    idx_list = df_current[mask].index.tolist()
    if not idx_list:
        st.error("ไม่พบรายการนี้ในไฟล์ Excel แล้ว อาจมีการลบหรือแก้ไขจากระบบหลัก")
    else:
        idx = idx_list[0]
        df_current.at[idx, "สถานะแจ้งซ่อม"] = maint_status
        if "บันทึกจากหน้างานล่าสุด" not in df_current.columns:
            df_current["บันทึกจากหน้างานล่าสุด"] = ""
        df_current.at[idx, "บันทึกจากหน้างานล่าสุด"] = note

        if uploaded_img is not None:
            filename = save_uploaded_image(uploaded_img, asset_code)
            if "รูปภาพครุภัณฑ์" not in df_current.columns:
                df_current["รูปภาพครุภัณฑ์"] = ""
            df_current.at[idx, "รูปภาพครุภัณฑ์"] = filename

        save_equipment_data(df_current)
        st.rerun()       # ✅ ใช้ st.rerun() แทน st.experimental_rerun()
