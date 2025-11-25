import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(
    page_title="ข้อมูลครุภัณฑ์ (QR)",
    page_icon="📋",
    layout="wide",
)

EXCEL_PRIMARY = DATA_DIR / DEFAULT_EXCEL_NAME
IMAGE_DIR = Path("asset_images")
QR_IMAGES_DIR = Path("qr_images")

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
QR_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

STATUS_MAINT_CHOICES = [
    "ยังไม่เคยแจ้งซ่อม",
    "แจ้งซ่อมแล้ว - กำลังดำเนินการ",
    "ซ่อมเสร็จแล้ว",
    "ปลดระวาง / รอจำหน่าย",
]


# ---------------------------
# Helper: Excel path + IO
# ---------------------------
def get_excel_path() -> Path | None:
    """
    ใช้ไฟล์เดียวกับ app.py:
      - DATA_DIR / DEFAULT_EXCEL_NAME เป็นหลัก
      - ถ้าไม่เจอ ลอง DEFAULT_EXCEL_PATH
    """
    if EXCEL_PRIMARY.exists():
        return EXCEL_PRIMARY
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH
    return None


def load_equipment_data() -> pd.DataFrame:
    path = get_excel_path()
    if path is None or not path.exists():
        return pd.DataFrame()

    df = pd.read_excel(path)
    df = df.dropna(how="all").reset_index(drop=True)

    # ให้แน่ใจว่ามีคอลัมน์ที่ใช้ร่วมกันกับ app.py
    if "สถานะแจ้งซ่อม" not in df.columns:
        df["สถานะแจ้งซ่อม"] = "ยังไม่เคยแจ้งซ่อม"
    if "รูปภาพครุภัณฑ์" not in df.columns:
        df["รูปภาพครุภัณฑ์"] = ""

    return df


def save_equipment_data(df: pd.DataFrame):
    path = get_excel_path()
    if path is None:
        st.error("ไม่พบไฟล์ Excel สำหรับบันทึกข้อมูล")
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


# ---------------------------
# Helper: โหลด / เซฟรูปครุภัณฑ์
# ---------------------------
def get_image_path_from_row(row: pd.Series) -> Path | None:
    val = str(row.get("รูปภาพครุภัณฑ์", "") or "").strip()
    if not val:
        return None

    p = Path(val)
    if not p.is_absolute():
        # เก็บแต่ชื่อไฟล์ใน Excel หมายถึงอยู่ในโฟลเดอร์ asset_images
        p = IMAGE_DIR / p.name
    return p


def save_uploaded_image(uploaded, asset_code: str) -> str:
    """
    เซฟไฟล์รูปที่อัปโหลดลงโฟลเดอร์ asset_images
    แล้วคืนค่าเป็นชื่อไฟล์ (เอาไปเก็บใน Excel)
    """
    suffix = Path(uploaded.name).suffix or ".png"
    safe_code = asset_code.replace("/", "_").replace("\\", "_").replace(" ", "_")
    filename = f"{safe_code}{suffix}"
    target_path = IMAGE_DIR / filename
    with open(target_path, "wb") as f:
        f.write(uploaded.getbuffer())
    return filename  # เก็บแค่ชื่อไฟล์


# ---------------------------
# Helper: โหลด QR image + ดาวน์โหลด
# ---------------------------
def get_qr_image_path_from_row(row: pd.Series) -> Path | None:
    """
    พยายามหา path QR จากคอลัมน์ใน Excel
    รองรับทั้ง '_qr_image_path' และ 'QR Code'
    """
    for col in ["_qr_image_path", "QR Code"]:
        if col in row.index:
            val = str(row.get(col, "") or "").strip()
            if not val:
                continue
            p = Path(val)
            if not p.is_absolute():
                # ส่วนใหญ่เราเก็บไว้ในโฟลเดอร์ qr_images
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


# ---------------------------
# MAIN PAGE
# ---------------------------
st.title("ข้อมูลเครื่องมือห้องปฏิบัติการ")

st.write(
    "หน้านี้ใช้สำหรับแก้ไขรายละเอียดครุภัณฑ์จากการสแกน QR Code "
    "ทุกคนที่มีลิงก์สามารถแก้ไขข้อมูลได้โดยไม่ต้องล็อกอิน"
)

# อ่าน query param จาก URL (เช่น ?code=LAB-AS-GN-A001)
try:
    query_params = st.query_params
except Exception:
    query_params = st.experimental_get_query_params()

if isinstance(query_params, dict):
    asset_code_from_url = query_params.get("code", [""])[0].strip()
else:
    asset_code_from_url = ""

df = load_equipment_data()
if df.empty:
    st.error("ไม่พบไฟล์ Excel สำหรับข้อมูลครุภัณฑ์ (ในโฟลเดอร์ data)")
    st.stop()

# ชื่อคอลัมน์ที่เก็บรหัสที่ใช้ใน QR
ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"

if ASSET_CODE_COL not in df.columns:
    st.error(f"ไม่พบคอลัมน์ '{ASSET_CODE_COL}' ในไฟล์ Excel")
    st.stop()

# ---------------------------
# หาแถวที่ตรงกับ code จาก URL
# ---------------------------
selected_index = None

if asset_code_from_url:
    matches = df.index[df[ASSET_CODE_COL].astype(str) == asset_code_from_url].tolist()
    if matches:
        selected_index = matches[0]

# ถ้าไม่มี code หรือหาไม่เจอ ให้เลือกจาก selectbox
def format_option(i: int) -> str:
    row = df.iloc[i]
    name = str(row.get("ชื่อ", "ไม่ทราบชื่อ"))
    code = str(row.get(ASSET_CODE_COL, ""))
    return f"{i+1:03d} - {name} ({code})"

all_indices = list(df.index)

if selected_index is None:
    # default row แรก
    selected_index = 0

st.markdown("### เลือกครุภัณฑ์ที่ต้องการแก้ไข")
selected_index = st.selectbox(
    "เลือกครุภัณฑ์จากรายการ",
    options=all_indices,
    index=selected_index,
    format_func=format_option,
    key="equip_select_public",
)

row = df.iloc[selected_index].copy()
asset_code = str(row.get(ASSET_CODE_COL, ""))

st.markdown("---")
st.markdown("### ฟอร์มรายละเอียด")

col_form_left, col_form_right = st.columns([1.4, 1])

# ---------------------------
# ฟอร์มข้อมูลทั่วไป
# ---------------------------
with col_form_left:
    # รายชื่อคอลัมน์ที่ให้แก้ไขได้ (เหมือนฝั่ง admin)
    editable_cols_order = [
        "ลำดับ",
        "ชื่อ",
        "ยี่ห้อ",
        ASSET_CODE_COL,
        "โมเดล",
        "หมายเลขเครื่อง",
        "ประเภทครุภัณฑ์",
        "ต้นทุนต่อหน่วย",
        "ชนิดของครุภัณฑ์",
        "สถานะ",
        "AssetID",
        "ปี",
        "สถานที่ใช้งาน (ปัจจุบัน)",
        "ผู้รับผิดชอบ (ปัจจุบัน)",
        "รหัสงานเครื่องมือแพทย์",
        "สถานะแจ้งซ่อม",
    ]

    updated_values: dict[str, str] = {}
    for col_name in editable_cols_order:
        if col_name not in df.columns:
            continue
        current_val = row.get(col_name, "")
        if col_name == "สถานะแจ้งซ่อม":
            current_str = "" if pd.isna(current_val) else str(current_val)
            if current_str not in STATUS_MAINT_CHOICES:
                current_str = STATUS_MAINT_CHOICES[0]
            new_val = st.selectbox(
                "สถานะแจ้งซ่อม",
                STATUS_MAINT_CHOICES,
                index=STATUS_MAINT_CHOICES.index(current_str),
                key=f"status_maint_{selected_index}",
            )
        else:
            new_val = st.text_input(
                col_name,
                value="" if pd.isna(current_val) else str(current_val),
                key=f"field_{col_name}_{selected_index}",
            )
        updated_values[col_name] = new_val

# ---------------------------
# ฝั่งขวา: QR Code + รูปภาพ + ดาวน์โหลด QR
# ---------------------------
with col_form_right:
    st.markdown("### QR Code ของครุภัณฑ์")

    # 1) พยายามใช้ไฟล์ QR จากโฟลเดอร์ / Excel ก่อน
    qr_path = get_qr_image_path_from_row(row)
    qr_bytes_for_download = None

    if qr_path and qr_path.exists():
        st.image(str(qr_path), use_column_width=True)
        with open(qr_path, "rb") as f:
            qr_bytes_for_download = f.read()
    else:
        # ถ้าไม่มีไฟล์ qr เก่า สร้างใหม่จาก URL ปัจจุบัน
        # (ใช้ base URL ของเว็บ public + code)
        url_for_qr = f"https://memsystemdashboard-qr.streamlit.app/?code={asset_code}"
        qr_bytes_for_download = generate_qr_bytes_for_url(url_for_qr)
        st.image(qr_bytes_for_download, use_column_width=True)

    st.caption(asset_code)
    st.write(
        "สแกน QR นี้เพื่อเปิดหน้าข้อมูลครุภัณฑ์จากอุปกรณ์อื่น ๆ ได้เช่นกัน"
    )

    if qr_bytes_for_download:
        st.download_button(
            "⬇️ ดาวน์โหลด QR (PNG)",
            data=qr_bytes_for_download,
            file_name=f"{asset_code}_qr.png",
            mime="image/png",
            use_container_width=True,
        )

    st.markdown("### รูปภาพครุภัณฑ์")

    current_image_path = get_image_path_from_row(row)
    if current_image_path and current_image_path.exists():
        st.image(str(current_image_path), caption="รูปภาพปัจจุบัน", use_column_width=True)
    else:
        st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")

    uploaded = st.file_uploader(
        "อัปโหลดรูปภาพใหม่ (ถ้าไม่เลือก ระบบจะใช้ของเดิม)",
        type=["png", "jpg", "jpeg"],
        key=f"upload_image_{selected_index}",
    )

# ---------------------------
# ปุ่มบันทึก
# ---------------------------
st.markdown("---")
if st.button("บันทึกการแก้ไข", type="primary", use_container_width=False):
    df_current = load_equipment_data()

    # เผื่อระหว่างโหลด-บันทึกมีคนลบ/เพิ่มแถว
    if selected_index >= len(df_current):
        st.error("แถวข้อมูลนี้ไม่อยู่ในตารางแล้ว กรุณารีเฟรชหน้าเว็บ")
        st.stop()

    # อัปเดตข้อมูลทั่วไป
    for col_name, new_val in updated_values.items():
        if col_name not in df_current.columns:
            continue

        orig_dtype = df_current[col_name].dtype
        if pd.api.types.is_numeric_dtype(orig_dtype):
            if new_val == "":
                df_current.at[selected_index, col_name] = pd.NA
            else:
                try:
                    df_current.at[selected_index, col_name] = pd.to_numeric(new_val)
                except Exception:
                    df_current.at[selected_index, col_name] = new_val
        else:
            df_current.at[selected_index, col_name] = new_val

    # ถ้ามีอัปโหลดรูปใหม่ -> เซฟไฟล์ แล้วเก็บชื่อไฟล์ในคอลัมน์ "รูปภาพครุภัณฑ์"
    if uploaded is not None:
        filename = save_uploaded_image(uploaded, asset_code)
        if "รูปภาพครุภัณฑ์" not in df_current.columns:
            df_current["รูปภาพครุภัณฑ์"] = ""
        df_current.at[selected_index, "รูปภาพครุภัณฑ์"] = filename

    # บันทึกลง Excel
    save_equipment_data(df_current)

    st.success("บันทึกการแก้ไขเรียบร้อยแล้ว (ทั้งหน้า QR และหน้าแอดมินจะเห็นข้อมูลเหมือนกัน)")
    st.experimental_rerun()
