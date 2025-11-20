# asset_qr_public.py
# หน้าแก้ไขรายละเอียดครุภัณฑ์จาก QR (สาธารณะ ไม่มีระบบล็อกอิน)

from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st
import qrcode

# ถ้าใช้ config.py ชุดเดียวกับแอปหลักอยู่ ให้ import มาด้วย
from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="รายละเอียดครุภัณฑ์ (QR)",
    page_icon="🔍",
    layout="wide",
)

# ⚠️ แก้ให้เป็น URL ของแอป "QR public" ตัวนี้หลังจากสร้างใน Streamlit Cloud แล้ว
# ตอนทดสอบในเครื่องให้ใช้ "http://localhost:8502"
QR_BASE_URL = "https://memsystemdashboard-qr.streamlit.app/"


# =========================
# โหลด / บันทึก Excel
# =========================
def get_excel_path() -> Path | None:
    """
    หาตำแหน่งไฟล์ Excel หลัก ถ้า DEFAULT_EXCEL_PATH มีอยู่ให้ใช้ตัวนั้น
    ถ้าไม่มีก็ลองหาไฟล์ .xls* ตัวแรกในโฟลเดอร์ data
    """
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    DATA_DIR.mkdir(exist_ok=True, parents=True)
    files = sorted(DATA_DIR.glob("*.xls*"))
    return files[0] if files else None


def load_data() -> tuple[pd.DataFrame | None, Path | None]:
    path = get_excel_path()
    if path is None or not path.exists():
        st.error("ไม่พบไฟล์ Excel สำหรับข้อมูลครุภัณฑ์ (ในโฟลเดอร์ data)")
        return None, None

    try:
        df = pd.read_excel(path)
        df = df.dropna(how="all").reset_index(drop=True)
        return df, path
    except Exception as e:
        st.error(f"อ่านไฟล์ Excel ไม่ได้: {e}")
        return None, path


def save_data(df: pd.DataFrame, path: Path):
    try:
        df.to_excel(path, index=False)
        st.success("✅ บันทึกข้อมูลเรียบร้อยแล้ว")
    except Exception as e:
        st.error(f"บันทึกไฟล์ Excel ไม่ได้: {e}")


# =========================
# Utils: ดึง code จาก URL
# =========================
def get_code_from_url() -> str:
    """
    ใช้ st.query_params (เวอร์ชันใหม่ แทน experimental_get_query_params)
    คาดว่า query รูปแบบ ?code=LAB-AS-GN-A001
    """
    params = st.query_params  # Mapping[str, List[str]]
    if "code" not in params:
        return ""
    val = params["code"]
    if isinstance(val, list):
        return (val[0] or "").strip()
    return str(val).strip()


# =========================
# แสดง QR จาก code
# =========================
def render_qr_card(asset_code: str):
    if not asset_code:
        st.info("ยังไม่ทราบรหัสเครื่องมือห้องปฏิบัติการ (code ใน URL)")
        return

    qr_url = f"{QR_BASE_URL}?code={asset_code}"

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    st.markdown(
        "<h4 style='text-align:center; margin-bottom:0.2rem;'>QR Code ของครุภัณฑ์</h4>",
        unsafe_allow_html=True,
    )
    st.image(buf, width=300)
    st.markdown(
        f"<p style='text-align:center; margin-top:0.4rem; color:#6b7280;'>"
        f"{asset_code}</p>",
        unsafe_allow_html=True,
    )
    st.caption("สแกน QR นี้เพื่อแก้ไขข้อมูลครุภัณฑ์จากอุปกรณ์อื่นๆ ได้เช่นกัน")


# =========================
# MAIN PAGE
# =========================
def main():
    st.markdown(
        """
        <h1 style="font-size:32px; margin-bottom:0.2rem;">
            ข้อมูลเครื่องมือห้องปฏิบัติการ
        </h1>
        <p style="color:#6b7280; margin-bottom:1.2rem;">
            หน้านี้ใช้สำหรับแก้ไขรายละเอียดครุภัณฑ์จากการสแกน QR Code
            ทุกคนที่มีลิงก์สามารถแก้ไขข้อมูลได้โดยไม่ต้องล็อกอิน
        </p>
        """,
        unsafe_allow_html=True,
    )

    df, excel_path = load_data()
    if df is None or excel_path is None:
        return

    # ชื่อคอลัมน์รหัสเครื่องมือใน Excel
    code_col = "รหัสเครื่องมือห้องปฏิบัติการ"
    if code_col not in df.columns:
        st.error(f"ไม่พบคอลัมน์ '{code_col}' ในไฟล์ Excel")
        return

    # -------------------------
    # เลือกแถวจาก code ใน URL
    # -------------------------
    url_code = get_code_from_url()

    if url_code:
        mask = df[code_col].astype(str).str.strip() == url_code
        if mask.any():
            selected_idx = int(df[mask].index[0])
        else:
            st.warning(
                f"ไม่พบรหัสเครื่องมือห้องปฏิบัติการ '{url_code}' ในไฟล์ Excel "
                "โปรดเลือกจากรายการด้านล่าง"
            )
            url_code = ""
            selected_idx = 0
    else:
        selected_idx = 0

    # ถ้าไม่มี code ใน URL ให้เลือกจาก selectbox
    if not url_code:
        options = list(df.index)

        def format_option(i: int) -> str:
            row = df.iloc[i]
            name = str(row.get("ชื่อ", "ไม่ทราบชื่อ"))
            code_val = str(row.get(code_col, ""))
            return f"{i+1:03d} - {name} ({code_val})"

        selected_idx = st.selectbox(
            "เลือกครุภัณฑ์ที่ต้องการแก้ไข",
            options=options,
            index=selected_idx,
            format_func=format_option,
        )

        url_code = str(df.loc[selected_idx, code_col])

    row = df.loc[selected_idx].copy()

    # -------------------------
    # Layout: ฟอร์ม + QR
    # -------------------------
    col_form, col_qr = st.columns([2.2, 1])

    with col_qr:
        render_qr_card(asset_code=url_code)

    with col_form:
        st.markdown(
            "<h3 style='margin-top:0;'>ฟอร์มรายละเอียด</h3>",
            unsafe_allow_html=True,
        )

        # แบ่งคอลัมน์ของฟอร์มเป็น 2 ฝั่ง
        columns_list = list(df.columns)
        half = (len(columns_list) + 1) // 2
        left_cols = columns_list[:half]
        right_cols = columns_list[half:]

        with st.form("asset_edit_form"):
            updated_values: dict[str, str] = {}

            c_left, c_right = st.columns(2)

            with c_left:
                for col in left_cols:
                    current_val = row.get(col, "")
                    updated_values[col] = st.text_input(
                        str(col),
                        value="" if pd.isna(current_val) else str(current_val),
                        key=f"left_{col}_{selected_idx}",
                    )

            with c_right:
                for col in right_cols:
                    current_val = row.get(col, "")
                    updated_values[col] = st.text_input(
                        str(col),
                        value="" if pd.isna(current_val) else str(current_val),
                        key=f"right_{col}_{selected_idx}",
                    )

            submitted = st.form_submit_button("บันทึกการแก้ไข")

            if submitted:
                # แปลงค่ากลับลง DataFrame
                for col, raw_val in updated_values.items():
                    if raw_val == "":
                        df.at[selected_idx, col] = pd.NA
                    else:
                        # พยายามแปลงเป็นตัวเลข ถ้าทำไม่ได้ค่อยเป็น string
                        try:
                            if pd.api.types.is_numeric_dtype(df[col].dtype):
                                df.at[selected_idx, col] = pd.to_numeric(raw_val)
                            else:
                                df.at[selected_idx, col] = raw_val
                        except Exception:
                            df.at[selected_idx, col] = raw_val

                save_data(df, excel_path)


if __name__ == "__main__":
    main()
