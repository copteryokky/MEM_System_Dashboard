# asset_qr_detail.py
# หน้า QR สำหรับให้ทุกคนแก้ไขข้อมูลครุภัณฑ์ได้ (ไม่ต้องล็อกอิน)

import streamlit as st
import pandas as pd
from pathlib import Path

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# =========================
# CONFIG + STYLE
# =========================
st.set_page_config(
    page_title="รายละเอียดครุภัณฑ์ (QR)",
    page_icon="🧪",
    layout="wide",
)

def set_style():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"]{
            background:#F3F4F6;
        }
        [data-testid="stHeader"]{
            background:transparent;
        }
        .block-container{
            max-width:1200px !important;
            padding-top:2.0rem !important;
            padding-bottom:2.0rem !important;
        }
        .qr-title{
            font-size:36px;
            font-weight:800;
            color:#111827;
            margin-bottom:0.25rem;
        }
        .qr-subtitle{
            font-size:13px;
            color:#6B7280;
            margin-bottom:1.5rem;
        }
        .qr-card{
            background:#FFFFFF;
            border-radius:28px;
            padding:20px 26px 26px 26px;
            box-shadow:0 22px 52px rgba(15,23,42,0.08);
            border:2px solid rgba(148,163,184,0.45);
        }
        .qr-card-title{
            font-size:20px;
            font-weight:700;
            margin-bottom:0.75rem;
            color:#111827;
        }
        .qr-label{
            font-size:13px !important;
            font-weight:500 !important;
            color:#4B5563 !important;
        }
        .qr-qrcode-box{
            text-align:center;
        }
        .qr-qrcode-sub{
            font-size:11px;
            color:#6B7280;
            margin-top:6px;
        }
        .qr-qrcode-code{
            font-size:12px;
            color:#111827;
            margin-top:6px;
            font-weight:600;
            letter-spacing:0.08em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================
# Excel helpers
# =========================
def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def find_excel_path() -> Path | None:
    """หาตำแหน่งไฟล์ Excel ในโฟลเดอร์ data"""
    ensure_data_dir()

    # 1) ใช้ DEFAULT_EXCEL_PATH ก่อน ถ้ามีอยู่
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    # 2) ถ้าไม่มี ลองหาไฟล์ .xls* ตัวแรกใน data
    files = sorted(DATA_DIR.glob("*.xls*"))
    if files:
        return files[0]

    return None


def load_equipment_df() -> tuple[pd.DataFrame | None, Path | None]:
    path = find_excel_path()
    if path is None or not path.exists():
        return None, None

    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)
        return df, path
    except Exception as e:
        st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
        return None, None


def save_equipment_df(df: pd.DataFrame, path: Path):
    try:
        ensure_data_dir()
        df.to_excel(path, index=False)
        st.success("บันทึกข้อมูลลงไฟล์ Excel เรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดขณะบันทึกไฟล์ Excel: {e}")

# =========================
# MAIN PAGE (ไม่ล็อกอิน)
# =========================
def main():
    set_style()

    st.markdown('<div class="qr-title">ข้อมูลเครื่องมือห้องปฏิบัติการ</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="qr-subtitle">หน้านี้ใช้สำหรับแก้ไขรายละเอียดครุภัณฑ์จากการสแกน QR Code ทุกคนที่เปิดลิงก์สามารถแก้ไขข้อมูลได้โดยไม่ต้องล็อกอิน</div>',
        unsafe_allow_html=True,
    )

    # ---------- โหลด Excel ----------
    df, excel_path = load_equipment_df()

    if df is None or excel_path is None:
        st.error("ไม่พบไฟล์ Excel สำหรับข้อมูลครุภัณฑ์ (ในโฟลเดอร์ data)")

        st.info("กรุณาอัปโหลดไฟล์ Excel (เช่น Smart Asset Lab.xlsx) เพื่อใช้เป็นฐานข้อมูลสำหรับหน้านี้")
        uploaded = st.file_uploader("อัปโหลดไฟล์ Excel", type=["xlsx", "xls"])

        if uploaded is not None:
            ensure_data_dir()
            save_path = DATA_DIR / DEFAULT_EXCEL_NAME
            try:
                with open(save_path, "wb") as f:
                    f.write(uploaded.getbuffer())
                st.success(f"บันทึกไฟล์ {uploaded.name} ไปที่ data/{DEFAULT_EXCEL_NAME} แล้ว")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"ไม่สามารถบันทึกไฟล์ได้: {e}")
        return  # จบฟังก์ชัน

    # ---------- ดึง code จาก URL ----------
    # st.query_params => dict-like (Streamlit เวอร์ชันใหม่)
    qp = st.query_params
    raw_code = qp.get("code")
    if isinstance(raw_code, list):
        raw_code = raw_code[0]
    asset_code = (raw_code or "").strip()

    # ---------- เลือกแถวจาก code ----------
    code_col = "รหัสเครื่องมือห้องปฏิบัติการ"
    if code_col not in df.columns:
        st.error(f"ไม่พบคอลัมน์ '{code_col}' ในไฟล์ Excel")
        st.stop()

    if asset_code:
        mask = df[code_col].astype(str) == asset_code
        if mask.any():
            idx = mask[mask].index[0]
        else:
            idx = 0
            st.warning(f"ไม่พบรหัสเครื่องมือห้องปฏิบัติการ '{asset_code}' ในไฟล์ Excel จะแสดงรายการลำดับที่ 1 แทน")
    else:
        idx = 0

    row = df.iloc[idx].copy()

    # ---------- UI: ฟอร์ม + QR ----------
    st.markdown('<div class="qr-card">', unsafe_allow_html=True)
    st.markdown('<div class="qr-card-title">ฟอร์มรายละเอียด</div>', unsafe_allow_html=True)

    col_form, col_qr = st.columns([2, 1])

    # ฟอร์มซ้าย
    with col_form:
        left_cols = []
        right_cols = []

        # แบ่งคอลัมน์ประมาณครึ่ง ๆ ให้ดูสวย
        cols = list(df.columns)
        half = (len(cols) + 1) // 2
        left_cols = cols[:half]
        right_cols = cols[half:]

        updated = {}

        lf, rf = st.columns(2)
        with lf:
            for col in left_cols:
                val = row.get(col, "")
                new_val = st.text_input(
                    col,
                    value="" if pd.isna(val) else str(val),
                    key=f"left_{col}_{idx}",
                    label_visibility="visible",
                )
                updated[col] = new_val

        with rf:
            for col in right_cols:
                val = row.get(col, "")
                new_val = st.text_input(
                    col,
                    value="" if pd.isna(val) else str(val),
                    key=f"right_{col}_{idx}",
                    label_visibility="visible",
                )
                updated[col] = new_val

        if st.button("บันทึกการแก้ไข", type="primary"):
            df_current, path_current = load_equipment_df()
            if df_current is None or path_current is None:
                st.error("ไม่สามารถโหลดไฟล์ Excel เพื่อบันทึกได้")
            else:
                for c in df_current.columns:
                    raw_val = updated.get(c, "")
                    # แปลงกลับเป็นตัวเลขถ้าเดิมเป็นตัวเลข
                    orig_dtype = df_current[c].dtype
                    if pd.api.types.is_numeric_dtype(orig_dtype):
                        if raw_val == "":
                            df_current.at[idx, c] = pd.NA
                        else:
                            try:
                                df_current.at[idx, c] = pd.to_numeric(raw_val)
                            except Exception:
                                df_current.at[idx, c] = raw_val
                    else:
                        df_current.at[idx, c] = raw_val

                save_equipment_df(df_current, path_current)
                st.experimental_rerun()

    # กล่อง QR ขวา
    with col_qr:
        st.markdown('<div class="qr-qrcode-box">', unsafe_allow_html=True)

        # พยายามโหลดไฟล์รูป QR ที่ generate ไว้ (ไม่มีก็ไม่เป็นไร)
        qr_path = None
        if "_qr_image_path" in df.columns:
            qr_path_str = str(row.get("_qr_image_path", "")).strip()
            if qr_path_str:
                p = Path(qr_path_str)
                if not p.is_absolute():
                    p = Path("qr_images") / p.name
                if p.exists():
                    qr_path = p

        if qr_path and qr_path.exists():
            st.image(str(qr_path), width=260)
        else:
            st.info("ไม่พบไฟล์รูป QR ในโฟลเดอร์ qr_images\n(ยังสามารถใช้ลิงก์จาก QR ที่สแกนมาได้ตามปกติ)")

        st.markdown(
            f"""
            <div class="qr-qrcode-sub">รหัสเครื่องมือห้องปฏิบัติการ</div>
            <div class="qr-qrcode-code">{asset_code or str(row.get(code_col, ''))}</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # จบ qr-card


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()
