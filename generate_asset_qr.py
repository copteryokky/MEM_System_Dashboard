# generate_asset_qr.py

import pandas as pd
import qrcode
from pathlib import Path
from urllib.parse import quote_plus

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# =========================
# ค่าคงที่
# =========================
EXCEL_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"   # คอลัมน์รหัสใน Excel

# ตอนทดสอบในเครื่อง ให้ใช้ "http://localhost:8501"
# ตอนใช้จริง ให้ใช้ URL ของแอปหลักใน Streamlit Cloud
# ตัวอย่าง: "https://mem-system-dashboard.streamlit.app"
QR_BASE_URL = "https://mem-system-dashboard.streamlit.app"

# โหมดสำหรับหน้า QR ใน app.py
QR_MODE_PARAM = "mode=qr"

OUTPUT_DIR = Path("qr_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# Helper: หาไฟล์ Excel
# =========================
def get_excel_path() -> Path | None:
    """คืน Path ของไฟล์ Excel ที่จะใช้สำหรับสร้าง QR"""
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_DIR.glob("*.xls*"))
    return files[0] if files else None


def load_df() -> pd.DataFrame:
    path = get_excel_path()
    if not path or not path.exists():
        raise FileNotFoundError("ไม่พบไฟล์ Excel สำหรับสร้าง QR")

    df = pd.read_excel(path)
    df = df.dropna(how="all").reset_index(drop=True)
    if EXCEL_CODE_COL not in df.columns:
        raise ValueError(f"ไม่พบคอลัมน์ '{EXCEL_CODE_COL}' ในไฟล์ {path}")
    return df


# =========================
# Helper: สร้าง QR รูปเดียว
# =========================
def make_qr(url: str, code: str, out_path: Path):
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out_path)
    print(f"สร้าง QR สำหรับ {code} → {out_path}")


# =========================
# main
# =========================
def main():
    df = load_df()

    for idx, row in df.iterrows():
        code = str(row[EXCEL_CODE_COL]).strip()
        if not code:
            continue

        # URL ที่จะถูก encode ลงใน QR
        # เช่น https://mem-system-dashboard.streamlit.app/?mode=qr&code=LAB-AS-GN-A001
        url = (
            f"{QR_BASE_URL}"
            f"?{QR_MODE_PARAM}&code={quote_plus(code)}"
        )

        filename = f"{idx+1:03d}_{code}.png"
        out_path = OUTPUT_DIR / filename
        make_qr(url, code, out_path)

    print("✅ สร้าง QR ครบแล้วในโฟลเดอร์ qr_images/")


if __name__ == "__main__":
    main()
