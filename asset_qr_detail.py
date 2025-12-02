import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"
IMAGE_DIR = Path("asset_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="ข้อมูลครุภัณฑ์จาก QR",
    page_icon="🔎",
    layout="wide",
)


def get_excel_path() -> Path | None:
    """เลือกไฟล์ Excel ที่ใช้เป็นฐานข้อมูล"""
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.xls*"))
    if not files:
        return None

    # ถ้ามีชื่อ DEFAULT_EXCEL_NAME ให้ใช้ก่อน
    for f in files:
        if f.name == DEFAULT_EXCEL_NAME:
            return f
    return files[0]


@st.cache_data
def load_equipment_data(path: str) -> pd.DataFrame:
    try:
        df = pd.read_excel(path).dropna(how="all").reset_index(drop=True)
        if "รูปภาพครุภัณฑ์" not in df.columns:
            df["รูปภาพครุภัณฑ์"] = ""
        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def get_image_path_from_row(row: pd.Series) -> Path | None:
    val = str(row.get("รูปภาพครุภัณฑ์", "") or "").strip()
    if not val:
        return None
    p = Path(val)
    if not p.is_absolute():
        p = IMAGE_DIR / p.name
    return p


def generate_qr_bytes(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ========= อ่าน query param =========
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

excel_path = get_excel_path()
if not excel_path or not excel_path.exists():
    st.error("ไม่พบไฟล์ Excel ฐานข้อมูลครุภัณฑ์")
    st.stop()

df = load_equipment_data(str(excel_path))
if df.empty or ASSET_CODE_COL not in df.columns:
    st.error("ไม่พบข้อมูลครุภัณฑ์ หรือไม่มีคอลัมน์รหัสเครื่องมือห้องปฏิบัติการในไฟล์ Excel")
    st.stop()

row_df = df[df[ASSET_CODE_COL].astype(str) == asset_code]
if row_df.empty:
    st.error(f"ไม่พบครุภัณฑ์ที่มีรหัส: {asset_code}")
    st.stop()

row = row_df.iloc[0]

# ========= ส่วนหัว =========
name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))
st.title(f"รหัสครุภัณฑ์: {asset_code}")
st.subheader(f"ชื่อครุภัณฑ์: {name}")

st.write("---")

# ========= แสดง QR + ปุ่มดาวน์โหลด =========
col_qr, col_info = st.columns([1, 1.2])

with col_qr:
    st.markdown("### QR Code ของครุภัณฑ์")
    # url ของหน้านี้เอง
    url_self = f"https://memsystemdashboard-qr.streamlit.app/?code={asset_code}"
    qr_bytes = generate_qr_bytes(url_self)
    st.image(qr_bytes, use_column_width=True)
    st.download_button(
        "ดาวน์โหลด QR (PNG)",
        data=qr_bytes,
        file_name=f"{asset_code}_qr.png",
        mime="image/png",
        use_container_width=True,
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

# ========= รูปภาพครุภัณฑ์ =========
st.markdown("## รูปภาพครุภัณฑ์")
img_path = get_image_path_from_row(row)
if img_path and img_path.exists():
    st.image(str(img_path), use_column_width=True)
else:
    st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")


st.caption(
    f"ข้อมูลอ้างอิงจากไฟล์ Excel: **{excel_path.name}**  "
    f"บันทึกไว้ในโฟลเดอร์ `data/` ของระบบหลัก"
)
