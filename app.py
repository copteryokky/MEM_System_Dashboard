import streamlit as st
import pandas as pd
from pathlib import Path
from io import BytesIO
import qrcode

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# ------------------------------
# ค่าคงที่ร่วมกัน
# ------------------------------
ASSET_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"
IMAGE_COL = "รูปภาพครุภัณฑ์"
NOTE_COL = "บันทึกจากหน้างานล่าสุด"  # ถ้าไม่มีจะสร้างให้

BASE_DIR = Path(__file__).parent

# โฟลเดอร์เก็บรูปครุภัณฑ์ (ใช้ร่วมกับเว็บหลักได้เลย)
IMAGE_DIR = BASE_DIR / "qr_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# แก้ URL นี้ให้ตรงกับ URL แอป QR ของคุณ
QR_BASE_URL = "https://mem-system-dashboard-qr.streamlit.app"

# ------------------------------
# ตั้งค่าเพจ
# ------------------------------
st.set_page_config(
    page_title="ข้อมูลครุภัณฑ์จาก QR",
    page_icon="🔎",
    layout="wide",
)


# ------------------------------
# ฟังก์ชันช่วยจัดการ Excel
# ------------------------------
def get_excel_path() -> Path | None:
    """
    หาไฟล์ Excel ฐานข้อมูลครุภัณฑ์
    ใช้ DEFAULT_EXCEL_PATH ก่อน ถ้ามี
    ถ้าไม่มีก็เลือกไฟล์ .xls* แรกในโฟลเดอร์ data
    """
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.xls*"))
    if not files:
        return None

    # ถ้ามีไฟล์ชื่อ DEFAULT_EXCEL_NAME ใช้อันนั้นก่อน
    for f in files:
        if f.name == DEFAULT_EXCEL_NAME:
            return f
    return files[0]


@st.cache_data
def _load_equipment_data(path_str: str, mtime: float) -> pd.DataFrame:
    """
    ฟังก์ชันโหลดข้อมูล (มี cache)
    ใช้ mtime ของไฟล์เป็นส่วนหนึ่งของ key
    เพื่อให้ถ้าไฟล์เปลี่ยนจะอ่านใหม่อัตโนมัติ
    """
    df = pd.read_excel(path_str).dropna(how="all").reset_index(drop=True)

    # ถ้าคอลัมน์รูป/บันทึกยังไม่มีให้สร้าง
    if IMAGE_COL not in df.columns:
        df[IMAGE_COL] = ""
    if NOTE_COL not in df.columns:
        df[NOTE_COL] = ""

    return df


def load_equipment_data(excel_path: Path) -> pd.DataFrame:
    mtime = excel_path.stat().st_mtime
    return _load_equipment_data(str(excel_path), mtime)


def save_equipment_data(df: pd.DataFrame, excel_path: Path) -> None:
    excel_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(excel_path, index=False)
    # เคลียร์ cache ของฟังก์ชันอ่าน
    _load_equipment_data.clear()


def get_image_path_from_row(row: pd.Series) -> Path | None:
    """
    แปลงค่าที่เก็บในคอลัมน์รูปภาพ ให้เป็น Path จริงในเครื่อง
    รองรับทั้ง path เต็ม และชื่อไฟล์เฉย ๆ
    """
    val = str(row.get(IMAGE_COL, "") or "").strip()
    if not val:
        return None

    p = Path(val)

    # ถ้าเป็น path สั้น ๆ / relative ให้ไปหาใน IMAGE_DIR
    if not p.is_absolute():
        p = IMAGE_DIR / p.name

    return p


def generate_qr_bytes(url: str) -> bytes:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ------------------------------
# หน้า Landing (ไม่มี code)
# ------------------------------
def render_landing():
    st.markdown(
        """
        <div style="
            text-align:center;
            padding: 2rem 0 1rem 0;
        ">
            <div style="
                display:inline-block;
                padding:0.35rem 1.2rem;
                border-radius:999px;
                background:rgba(25, 118, 210, 0.08);
                color:#0D47A1;
                font-size:0.9rem;
                margin-bottom:1.2rem;
            ">
                ระบบข้อมูลครุภัณฑ์จาก QR Code
            </div>
            <h1 style="font-size:2.2rem; margin-bottom:0.3rem;">
                สแกน QR จากสติ๊กเกอร์บนครุภัณฑ์<br/>
                เพื่อดูข้อมูลและอัปเดตสถานะจากหน้างาน
            </h1>
            <p style="color:#4B5563; max-width:720px; margin:0 auto 1.5rem auto;">
                หน้านี้ถูกออกแบบมาสำหรับบุคลากรที่สแกน QR จากสติ๊กเกอร์บนเครื่องมือแพทย์หรือครุภัณฑ์ 
                เพื่อเปิดดูรายละเอียดล่าสุด อัปโหลดรูป และบันทึกข้อมูลจากหน้างาน 
                ข้อมูลที่บันทึกจะแชร์ร่วมกับระบบหลักแบบใกล้เคียง Real-time
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            """
            <div style="
                background:white;
                border-radius:1.2rem;
                padding:1.2rem 1.4rem;
                box-shadow:0 12px 30px rgba(15,23,42,0.06);
                border:1px solid rgba(148,163,184,0.35);
                height:100%;
            ">
                <h3 style="margin-top:0; margin-bottom:0.4rem; font-size:1.05rem;">
                    1. ติด QR บนครุภัณฑ์
                </h3>
                <p style="font-size:0.9rem; color:#4B5563;">
                    ใช้ระบบหลักสร้าง QR Code ตามรหัสครุภัณฑ์ แล้วนำไปพิมพ์และติดบนเครื่องจริง
                    ให้จุดสแกนอยู่ใกล้ป้ายระบุชื่อและรหัสครุภัณฑ์
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            """
            <div style="
                background:white;
                border-radius:1.2rem;
                padding:1.2rem 1.4rem;
                box-shadow:0 12px 30px rgba(15,23,42,0.06);
                border:1px solid rgba(148,163,184,0.35);
                height:100%;
            ">
                <h3 style="margin-top:0; margin-bottom:0.4rem; font-size:1.05rem;">
                    2. สแกนด้วยมือถือ / แท็บเล็ต
                </h3>
                <p style="font-size:0.9rem; color:#4B5563;">
                    เปิดกล้องหรือแอปสแกน QR แล้วสแกนสติ๊กเกอร์ 
                    ระบบจะพามาที่หน้านี้โดยอัตโนมัติ พร้อมระบุรหัสครุภัณฑ์ใน URL
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            """
            <div style="
                background:white;
                border-radius:1.2rem;
                padding:1.2rem 1.4rem;
                box-shadow:0 12px 30px rgba(15,23,42,0.06);
                border:1px solid rgba(148,163,184,0.35);
                height:100%;
            ">
                <h3 style="margin-top:0; margin-bottom:0.4rem; font-size:1.05rem;">
                    3. ดูข้อมูล + อัปเดตจากหน้างาน
                </h3>
                <p style="font-size:0.9rem; color:#4B5563;">
                    เจ้าหน้าที่สามารถดูข้อมูลล่าสุด อัปโหลดรูปภาพสภาพปัจจุบัน 
                    และบันทึกโน้ตจากการตรวจสอบหรือการใช้งาน 
                    ซึ่งจะแชร์ให้ระบบหลักเห็นเหมือนกัน
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    st.info(
        "หากต้องการทดสอบเอง สามารถลองเปิด URL นี้พร้อมพารามิเตอร์ `?code=รหัสครุภัณฑ์` "
        "เช่น `...?code=LAB-AS-GN-A001`"
    )


# ------------------------------
# หน้าแสดงรายละเอียดจาก QR
# ------------------------------
def render_asset_detail(asset_code: str):
    excel_path = get_excel_path()
    if not excel_path or not excel_path.exists():
        st.error("ไม่พบไฟล์ Excel ฐานข้อมูลครุภัณฑ์ในโฟลเดอร์ data/")
        st.stop()

    df = load_equipment_data(excel_path)
    if df.empty or ASSET_CODE_COL not in df.columns:
        st.error(
            "ไม่พบข้อมูลครุภัณฑ์ หรือไม่มีคอลัมน์รหัสเครื่องมือห้องปฏิบัติการในไฟล์ Excel"
        )
        st.stop()

    mask = df[ASSET_CODE_COL].astype(str) == asset_code
    if not mask.any():
        st.error(f"ไม่พบครุภัณฑ์ที่มีรหัส: {asset_code}")
        st.stop()

    row_index = df.index[mask][0]
    row = df.loc[row_index]

    # -------- ส่วนหัว --------
    name = str(row.get("ชื่อ", "ไม่พบชื่อครุภัณฑ์"))
    st.title(f"รหัสครุภัณฑ์: {asset_code}")
    st.subheader(f"ชื่อครุภัณฑ์: {name}")

    st.write("---")

    # -------- QR + ข้อมูลสรุป --------
    col_qr, col_info = st.columns([1, 1.2])

    with col_qr:
        st.markdown("### QR Code ของครุภัณฑ์")

        url_self = f"{QR_BASE_URL}/?code={asset_code}"
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

    # -------- รูปภาพ + ฟอร์มแก้ไข --------
    st.markdown("## รูปภาพครุภัณฑ์")

    img_path = get_image_path_from_row(row)
    if img_path and img_path.exists():
        st.image(str(img_path), use_column_width=True)
    else:
        st.info("ยังไม่มีรูปภาพสำหรับรายการนี้")

    st.markdown("### อัปเดตรูปภาพ / บันทึกจากหน้างาน")

    uploaded_file = st.file_uploader(
        "เลือกรูปครุภัณฑ์ (PNG / JPG / JPEG)",
        type=["png", "jpg", "jpeg"],
        help="ถ้าไม่เลือกรูป ระบบจะใช้รูปเดิมตามที่บันทึกไว้ในไฟล์ Excel",
    )

    current_note = str(row.get(NOTE_COL, "") or "")
    note_text = st.text_area(
        "บันทึกจากหน้างาน (เช่น สภาพปัจจุบัน, ปัญหาที่พบ ฯลฯ)",
        value=current_note,
        placeholder="กรอกบันทึกจากหน้างานที่นี่",
    )

    if st.button("บันทึกการแก้ไข", use_container_width=True):
        # --- อัปเดตรูป ---
        if uploaded_file is not None:
            ext = Path(uploaded_file.name).suffix.lower()
            filename = f"{asset_code}{ext}"
            save_path = IMAGE_DIR / filename

            with open(save_path, "wb") as f:
                f.write(uploaded_file.read())

            # เก็บ path ไว้ใน Excel (ใช้ path relative)
            df.loc[row_index, IMAGE_COL] = str(save_path.relative_to(BASE_DIR))

        # --- อัปเดตบันทึกจากหน้างาน ---
        df.loc[row_index, NOTE_COL] = note_text

        # เวลาอัปเดตล่าสุด เผื่อเอาไปโชว์ในเว็บหลัก
        df.loc[row_index, "อัปเดตจากหน้างานล่าสุด"] = pd.Timestamp.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # เซฟกลับเข้า Excel (แชร์กับเว็บหลัก)
        save_equipment_data(df, excel_path)

        st.success(
            "บันทึกการแก้ไขเรียบร้อยแล้ว (ทั้งหน้า QR และหน้าเว็บหลักจะเห็นข้อมูลชุดเดียวกัน)"
        )

        # รีเฟรชหน้าให้โหลดข้อมูล/รูปใหม่
        st.rerun()

    st.caption(
        f"ข้อมูลอ้างอิงจากไฟล์ Excel: **{excel_path.name}** "
        f"(เก็บไว้ในโฟลเดอร์ `data/` ของระบบหลัก และใช้ร่วมกันกับเว็บแดชบอร์ดหลัก)"
    )


# ------------------------------
# main
# ------------------------------
def main():
    # อ่าน query param
    try:
        query_params = st.query_params  # Streamlit รุ่นใหม่
    except Exception:
        query_params = st.experimental_get_query_params()

    if isinstance(query_params, dict):
        asset_code = query_params.get("code", [""])[0].strip()
    else:
        asset_code = ""

    if not asset_code:
        # ไม่มี code → แสดงหน้า Landing
        render_landing()
    else:
        # มี code → แสดงหน้าอ่าน/แก้ไขข้อมูลจาก QR
        render_asset_detail(asset_code)


if __name__ == "__main__":
    main()
