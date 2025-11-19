# generate_asset_qr.py

import pandas as pd
from pathlib import Path
from urllib.parse import quote_plus

import qrcode
from PIL import Image, ImageDraw, ImageFont

from config import DATA_DIR, DEFAULT_EXCEL_NAME, DEFAULT_EXCEL_PATH

# =========================
# CONFIG
# =========================
EXCEL_CODE_COL = "รหัสเครื่องมือห้องปฏิบัติการ"

# URL ของหน้า Streamlit ที่ใช้แสดง/แก้ไขรายละเอียดครุภัณฑ์ (asset_qr_detail.py ที่ deploy แล้ว)
QR_BASE_URL = "https://mem-system-qr.streamlit.app"  # <-- แก้ให้ตรงของคุณ
QR_PAGE_PATH = ""  # ถ้าใช้ root ก็เว้นว่าง "", ถ้าเป็น /asset ก็ใส่ "/asset"

OUTPUT_DIR = Path("qr_images")
OUTPUT_DIR.mkdir(exist_ok=True)

# ถ้ามีฟอนต์ TH Sarabun ในเครื่องให้ใส่ path ตรงนี้
# ถ้าไม่ใส่ จะใช้ฟอนต์ default ของ PIL
FONT_PATH = None  # ตัวอย่าง: FONT_PATH = "THSarabunNew.ttf"


# =========================
# Helper: หาไฟล์ Excel
# =========================
def get_excel_path() -> Path | None:
    """คืน path ของไฟล์ Excel ที่จะใช้สร้าง QR"""
    # ใช้ไฟล์ default ก่อน ถ้ามีอยู่
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    # ถ้าไม่มี ให้ลองหา *.xls* ใน DATA_DIR
    files = sorted(DATA_DIR.glob("*.xls*"))
    if files:
        print(f"พบไฟล์ Excel: {files[0].name}")
        return files[0]

    return None


def load_df() -> pd.DataFrame:
    path = get_excel_path()
    if not path or not path.exists():
        raise FileNotFoundError("ไม่พบไฟล์ Excel สำหรับสร้าง QR")

    print(f"อ่านข้อมูลจาก: {path}")
    df = pd.read_excel(path)
    df = df.dropna(how="all").reset_index(drop=True)

    if EXCEL_CODE_COL not in df.columns:
        raise KeyError(f"ไม่พบคอลัมน์ '{EXCEL_CODE_COL}' ในไฟล์ Excel")

    return df


# =========================
# Helper: โหลดฟอนต์
# =========================
def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """โหลดฟอนต์ ถ้าไม่เจอไฟล์จะใช้ default ของ PIL แทน"""
    if FONT_PATH and Path(FONT_PATH).exists():
        try:
            return ImageFont.truetype(FONT_PATH, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


# =========================
# สร้างรูป QR + ตัวหนังสือด้านบน/ล่าง
# =========================
def make_qr_with_text(url: str, code: str, out_path: Path):
    # สร้าง qr object
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_w, qr_h = qr_img.size

    # สร้าง canvas สูงกว่ารูป qr เพื่อใส่ตัวอักษรด้านบน/ล่าง
    padding_top = 40
    padding_bottom = 60
    canvas_h = qr_h + padding_top + padding_bottom
    img = Image.new("RGB", (qr_w, canvas_h), "white")

    # วาง QR กลางแนวตั้ง
    img.paste(qr_img, (0, padding_top))

    draw = ImageDraw.Draw(img)

    # ==== ข้อความด้านบน: code เช่น LAB-AS-GN-A001 ====
    title_font = get_font(26)
    title_text = code

    # Pillow ใหม่ใช้ textbbox แทน textsize
    bbox_title = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = bbox_title[2] - bbox_title[0]
    title_x = (qr_w - title_w) // 2
    title_y = 8  # ห่างจากขอบบน

    draw.text((title_x, title_y), title_text, font=title_font, fill=(0, 0, 0))

    # ==== ข้อความด้านล่าง: คำอธิบาย ====
    footer_font = get_font(18)
    footer_text = "สแกนเพื่อเปิดดู/แก้ไขรายละเอียดครุภัณฑ์"

    bbox_footer = draw.textbbox((0, 0), footer_text, font=footer_font)
    footer_w = bbox_footer[2] - bbox_footer[0]
    footer_x = (qr_w - footer_w) // 2
    footer_y = padding_top + qr_h + 8

    draw.text((footer_x, footer_y), footer_text, font=footer_font, fill=(0, 0, 0))

    # บันทึกไฟล์
    img.save(out_path)
    print(f"สร้าง QR สำหรับ {code} -> {out_path}")


# =========================
# MAIN
# =========================
def main():
    df = load_df()

    # เลือกเฉพาะแถวที่มีรหัสเครื่องมือห้องปฏิบัติการ
    df_codes = df[[EXCEL_CODE_COL]].dropna().reset_index(drop=True)

    if df_codes.empty:
        print(f"ไม่มีข้อมูลในคอลัมน์ '{EXCEL_CODE_COL}'")
        return

    for idx, row in df_codes.iterrows():
        code = str(row[EXCEL_CODE_COL]).strip()
        if not code:
            continue

        # เข้ารหัส code ลงใน query string
        encoded = quote_plus(code)

        # เช่น https://mem-system-qr.streamlit.app?code=LAB-AS-GN-A001
        url = f"{QR_BASE_URL}{QR_PAGE_PATH}?code={encoded}"

        # ตั้งชื่อไฟล์ให้มีลำดับนำหน้า
        out_name = f"{idx+1:03d}_{code}.png"
        out_path = OUTPUT_DIR / out_name

        make_qr_with_text(url, code, out_path)

    print("\n✅ เสร็จแล้ว! รูป QR ถูกสร้างในโฟลเดอร์ 'qr_images'")


if __name__ == "__main__":
    main()
