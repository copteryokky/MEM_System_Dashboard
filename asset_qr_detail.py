import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# ---------------------------------
# ค่าคงที่ / โฟลเดอร์เก็บรูป
# ---------------------------------
ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"
IMAGE_DIR = Path("asset_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="ข้อมูลครุภัณฑ์จาก QR",
    page_icon="🔎",
    layout="wide",
)


# ---------------------------------
# ฟังก์ชันจัดการไฟล์ Excel
# ---------------------------------
def get_excel_path() -> Path | None:
    """เลือกไฟล์ Excel ที่ใช้เป็นฐานข้อมูลหลัก"""
    # ถ้าระบุ DEFAULT_EXCEL_PATH ไว้ และมีอยู่จริง ให้ใช้ตัวนั้นก่อน
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
    """โหลดข้อมูลครุภัณฑ์จาก Excel"""
    try:
        df = pd.read_excel(path).dropna(how="all").reset_index(drop=True)
        if "รูปภาพครุภัณฑ์" not in df.columns:
            df["รูปภาพครุภัณฑ์"] = ""
        return df
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return pd.DataFrame()


def save_equipment_data(df: pd.DataFrame, path: Path) -> None:
    """บันทึก DataFrame กลับลง Excel"""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


# ---------------------------------
# ฟังก์ชันเกี่ยวกับรูป / QR
# ---------------------------------
def get_image_path_from_row(row: pd.Series) -> Path | None:
    """อ่าน path ของรูปจากแถวข้อมูล แล้วชี้ไปที่โฟลเดอร์ asset_images"""
    val = str(row.get("รูปภาพครุภัณฑ์", "") or "").strip()
    if not val:
        return None
    p = Path(val)
    # ให้ map เข้าโฟลเดอร์ asset_images เสมอ
    if not p.is_absolute():
        p = IMAGE_DIR / p.name
    return p


def save_uploaded_image(file, asset_code: str) -> Path | None:
    """บันทึกรูปที่อัปโหลดเข้ามา ลงโฟลเดอร์ asset_images"""
    if not file:
        return None
    suffix = Path(file.name).suffix or ".png"
    filename = f"{asset_code}{suffix}"
    save_path = IMAGE_DIR / filename
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    return save_path


def generate_qr_bytes(url: str) -> bytes:
    """สร้างรูป QR จาก URL แล้วคืนค่าเป็น bytes (PNG)"""
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------
# อ่าน query param จาก URL
# ---------------------------------
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

# ---------------------------------
# โหลดข้อมูลจาก Excel
# ---------------------------------
excel_path = get_excel_path()
if not excel_path or not excel_path.exists():
    st.error("ไม่พบไฟล์ Excel ฐานข้อมูลครุภัณฑ์")
    st.stop()

df = load_equipment_data(str(excel_path))
if df.empty or ASSET_CODE_COL not in df.columns:
    st.error(
        "ไม่พบข้อมูลครุภัณฑ์ หรือไม่มีคอลัมน์ "
        f"`{ASSET_CODE_COL}` ในไฟล์ Excel"
    )
    st.stop()

row_df = df[df[ASSET_CODE_COL].astype(str) == asset_code]
if row_df.empty:
    st.error(f"ไม่พบครุภัณฑ์ที่มีรหัส: {asset_code}")
    st.stop()

# แถวข้อมูลของครุภัณฑ์ที่ต้องการ
row = row_df.iloc[0]
row_index = row_df.index[0]

# ---------------------------------
# ส่วนหัวหน้าจอ
# ---------------------------------
name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))

st.markdown(
    f"""
    <div style="margin-bottom:0.4rem;">
        <h2 style="margin-bottom:0.2rem;">รหัสครุภัณฑ์: {asset_code}</h2>
        <h4 style="color:#4b5563; margin-top:0;">ชื่อครุภัณฑ์: {name}</h4>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"ข้อมูลดึงจากไฟล์ Excel: `{excel_path.name}` (โฟลเดอร์ data ของระบบหลัก)")

st.write("---")

# ---------------------------------
# Layout หลัก (QR + ข้อมูล + รูปภาพ)
# ---------------------------------
left, right = st.columns([1, 1.1])

with left:
    # --------- QR Code ----------
    st.subheader("QR Code ของครุภัณฑ์")

    # URL ของหน้านี้เอง (เติมโดเมนของเว็บ QR ให้ตรงกับที่ใช้จริง)
    # แก้ให้ตรงกับโดเมนของคุณ เช่น mem-system-dashboard-qr.streamlit.app
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

    st.write("")
    # --------- ข้อมูลสรุป ----------
    st.subheader("ข้อมูลสรุปครุภัณฑ์")

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

with right:
    # --------- รูปภาพ ----------
    st.subheader("รูปภาพครุภัณฑ์")

    current_img_path = get_image_path_from_row(row)
    if current_img_path and current_img_path.exists():
        st.image(str(current_img_path), use_column_width=True, caption="รูปปัจจุบัน")
    else:
        st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")

    st.markdown("#### อัปโหลดรูปภาพใหม่")
    uploaded = st.file_uploader(
        "เลือกไฟล์รูป (PNG / JPG / JPEG)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
    )

    if st.button("บันทึกการแก้ไขรูปภาพ", type="primary"):
        if uploaded is None:
            st.warning("กรุณาเลือกไฟล์รูปก่อน")
        else:
            # บันทึกรูปลงโฟลเดอร์ asset_images
            save_path = save_uploaded_image(uploaded, asset_code)

            # อัปเดต path (เก็บแค่ชื่อไฟล์) ลงใน DataFrame
            df.at[row_index, "รูปภาพครุภัณฑ์"] = save_path.name

            # บันทึกกลับไปที่ Excel หลัก
            save_equipment_data(df, excel_path)

            # เคลียร์ cache แล้ว reload ใหม่เพื่อให้เห็นผลทันที
            load_equipment_data.clear()
            st.success(
                "บันทึกรูปภาพเรียบร้อยแล้ว "
                "(ระบบที่ใช้ไฟล์ Excel เดียวกันจะเห็นข้อมูลตรงกันอัตโนมัติ)"
            )
            st.rerun()

st.write("---")
st.caption(
    "หมายเหตุ: หน้า QR นี้แก้ไขข้อมูลในไฟล์ Excel เดียวกับระบบหลัก "
    "ถ้าระบบหลัก/เว็บอื่นใช้ไฟล์คนละชุดหรือคนละเซิร์ฟเวอร์ ข้อมูลจะไม่ซิงค์กันนะครับ"
)
