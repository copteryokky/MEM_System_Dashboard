import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# =========================
# CONFIG / CONSTANTS
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
# Excel Helpers (ให้ logic คล้าย app.py)
# =========================
def get_current_excel_path() -> Path | None:
    """
    ใช้ DEFAULT_EXCEL_PATH เป็นหลัก
    ถ้าไม่มีให้มองหาไฟล์ .xls* ในโฟลเดอร์ data
    """
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
        st.error("ยังไม่ได้กำหนดไฟล์ Excel สำหรับบันทึกข้อมูล")
        return

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_excel(path, index=False)
        st.success(f"บันทึกข้อมูลลงไฟล์: {path.name} เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")


# =========================
# รูปภาพ & QR helpers
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


def generate_qr_bytes(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# =========================
# อ่าน query param จาก URL (?code=...)
# =========================
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

# =========================
# โหลดข้อมูลจาก Excel
# =========================
excel_path = get_current_excel_path()
if not excel_path or not excel_path.exists():
    st.error("ไม่พบไฟล์ Excel ฐานข้อมูลครุภัณฑ์")
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
row_index = row_df.index[0]

# =========================
# UI – ส่วนหัว
# =========================
name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))
st.title(f"รหัสครุภัณฑ์: {asset_code}")
st.subheader(f"ชื่อครุภัณฑ์: {name}")

st.caption(
    f"ข้อมูลจากไฟล์ Excel: **{excel_path.name}**  "
    f"(โฟลเดอร์ `data/` ของระบบ)"
)

st.write("---")

# =========================
# QR Code + ข้อมูลสรุป
# =========================
col_qr, col_info = st.columns([1, 1.2])

with col_qr:
    st.markdown("### QR Code ของครุภัณฑ์")
    url_self = f"https://memsystemdashboard-qr.streamlit.app/?code={asset_code}"
    qr_bytes = generate_qr_bytes(url_self)
    st.image(qr_bytes, use_column_width=True)
    st.download_button(
        "⬇️ ดาวน์โหลด QR (PNG)",
        data=qr_bytes,
        file_name=f"{asset_code}_qr.png",
        mime="image/png",
        use_container_width=True,
    )
    st.caption("สามารถนำ QR นี้ไปติดที่ตัวอุปกรณ์เพื่อใช้สแกนเปิดหน้าข้อมูลนี้ได้")


with col_info:
    st.markdown("### ข้อมูลสรุปครุภัณฑ์")

    cols_left = [
        "ชื่อ",
        "รุ่น",
        "หมายเลขเครื่อง",
        "AssetID",
        "สถานะ",
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
# แก้ไขข้อมูลจากหน้างาน (มือถือ)
# =========================
st.markdown("## แก้ไขข้อมูลจากหน้างาน")

# สถานะแจ้งซ่อม
current_maint = str(row.get("สถานะแจ้งซ่อม", MAINT_STATUS_CHOICES[0]) or "")
if current_maint not in MAINT_STATUS_CHOICES:
    current_maint = MAINT_STATUS_CHOICES[0]

maint_status = st.selectbox(
    "สถานะแจ้งซ่อม",
    MAINT_STATUS_CHOICES,
    index=MAINT_STATUS_CHOICES.index(current_maint),
)

# บันทึก / หมายเหตุ หน้างาน
current_note = str(row.get("บันทึกจากหน้างานล่าสุด", "") or "")
note = st.text_area(
    "บันทึกจากหน้างาน (เช่น อาการเสีย / สิ่งที่ตรวจพบ)",
    value=current_note,
    height=100,
)

# รูปภาพครุภัณฑ์
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

    # หา index อีกครั้ง เผื่อไฟล์มีการแก้ไขระหว่างนั้น
    mask = df_current[ASSET_CODE_COL].astype(str) == asset_code
    idx_list = df_current[mask].index.tolist()
    if not idx_list:
        st.error("ไม่พบรายการนี้ในไฟล์ Excel แล้ว อาจมีการลบหรือแก้ไขจากระบบหลัก")
    else:
        idx = idx_list[0]

        # อัปเดตสถานะแจ้งซ่อม + บันทึกจากหน้างาน
        df_current.at[idx, "สถานะแจ้งซ่อม"] = maint_status
        if "บันทึกจากหน้างานล่าสุด" not in df_current.columns:
            df_current["บันทึกจากหน้างานล่าสุด"] = ""
        df_current.at[idx, "บันทึกจากหน้างานล่าสุด"] = note

        # ถ้าอัปโหลดรูปใหม่
        if uploaded_img is not None:
            filename = save_uploaded_image(uploaded_img, asset_code)
            if "รูปภาพครุภัณฑ์" not in df_current.columns:
                df_current["รูปภาพครุภัณฑ์"] = ""
            df_current.at[idx, "รูปภาพครุภัณฑ์"] = filename

        save_equipment_data(df_current)

        st.success("บันทึกการแก้ไขเรียบร้อยแล้ว (เว็บหลักและหน้า QR จะเห็นข้อมูลเหมือนกัน)")
        st.rerun()
