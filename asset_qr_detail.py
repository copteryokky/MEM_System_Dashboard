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


# ----------------------------- #
#  ฟังก์ชันจัดการไฟล์ Excel
# ----------------------------- #
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


def save_equipment_data(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)


# ----------------------------- #
#  รูป / QR
# ----------------------------- #
def get_image_path_from_row(row: pd.Series) -> Path | None:
    val = str(row.get("รูปภาพครุภัณฑ์", "") or "").strip()
    if not val:
        return None
    p = Path(val)
    # ให้เก็บจริงในโฟลเดอร์ asset_images เสมอ
    if not p.is_absolute():
        p = IMAGE_DIR / p.name
    return p


def save_uploaded_image(file, asset_code: str) -> Path | None:
    if not file:
        return None
    suffix = Path(file.name).suffix or ".png"
    filename = f"{asset_code}{suffix}"
    save_path = IMAGE_DIR / filename
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())
    return save_path


def generate_qr_bytes(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ----------------------------- #
#  อ่านค่า code จาก URL
# ----------------------------- #
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

# ----------------------------- #
#  โหลดข้อมูลจาก Excel
# ----------------------------- #
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

row = row_df.iloc[0]
row_index = row_df.index[0]

# ----------------------------- #
#  UI ส่วนหัว
# ----------------------------- #
name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))
st.markdown(
    f"""
    <h2 style="margin-bottom:0.2rem;">รหัสครุภัณฑ์: {asset_code}</h2>
    <h4 style="color:#4b5563; margin-top:0;">ชื่อครุภัณฑ์: {name}</h4>
    """,
    unsafe_allow_html=True,
)
st.caption(f"ข้อมูลจากไฟล์ Excel: `{excel_path.name}`")

st.write("---")

# ----------------------------- #
#   QR + ข้อมูล / รูปภาพ
# ----------------------------- #
left, right = st.columns([1, 1.1])

with left:
    st.subheader("QR Code ของครุภัณฑ์")

    # url ของหน้านี้เอง (ใช้โดเมนของเว็บ QR นี้)
    url_self = f"{st.get_option('server.baseUrlPath') or ''}"
    # ถ้ารันบน Streamlit Cloud url_self จะว่าง ให้ใช้โดเมนจากเบราว์เซอร์แทน
    url_self = f"{st.experimental_get_query_params()}"
    # ง่ายสุด: เขียนตรง ๆ ตามโดเมนที่ใช้จริง
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
            save_path = save_uploaded_image(uploaded, asset_code)
            # อัปเดตลง DataFrame และบันทึกกลับไปที่ Excel
            df.at[row_index, "รูปภาพครุภัณฑ์"] = save_path.name
            save_equipment_data(df, excel_path)
            # ล้าง cache แล้วรันใหม่เพื่อให้เห็นรูปล่าสุด
            load_equipment_data.clear()
            st.success("บันทึกรูปภาพเรียบร้อยแล้ว (หน้าเว็บหลักที่ใช้ Excel เดียวกันจะเห็นข้อมูลตรงกัน)")
            st.rerun()

st.write("---")
st.caption(
    "หมายเหตุ: หน้า QR นี้จะอัปเดตข้อมูลในไฟล์ Excel เดียวกับระบบหลัก "
    "ถ้าเว็บหลักใช้ไฟล์คนละชุดหรือคนละเครื่องกัน ข้อมูลจะไม่เชื่อมกันนะครับ"
)
