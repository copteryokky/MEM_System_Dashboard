# config.py
from pathlib import Path

# โฟลเดอร์หลักของโปรเจกต์ (ตำแหน่งเดียวกับ app.py)
BASE_DIR = Path(__file__).resolve().parent

# โฟลเดอร์เก็บไฟล์ Excel
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_excel_path() -> Path:
    """
    คืน Path ของไฟล์ Excel กลางที่ระบบใช้จริง
    - มองหาไฟล์ .xls / .xlsx / .xlsm ในโฟลเดอร์ data
    - ถ้ามีหลายไฟล์ เลือกไฟล์ที่ขนาดใหญ่สุด (มักจะเป็นไฟล์หลัก ไม่ใช่ไฟล์เสีย)
    - ถ้าไม่พบเลย จะคืน path ชื่อ Smart.xlsx (ให้คุณเอา Excel หลักมาตั้งชื่อแบบนี้)
    """
    candidates = [p for p in DATA_DIR.glob("*.xls*") if p.is_file()]

    if not candidates:
        # กรณีไม่มีไฟล์เลย ให้เตรียมชื่อ default ไว้ (คุณสามารถเปลี่ยนชื่อได้)
        return DATA_DIR / "Smart.xlsx"

    # เลือกไฟล์ที่ขนาดใหญ่สุด เผื่อมีไฟล์ทดลอง / ไฟล์ไม่สมบูรณ์ปนอยู่
    candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]


# ค่าที่ไฟล์อื่น ๆ ใช้ร่วมกัน
DEFAULT_EXCEL_PATH = get_excel_path()
DEFAULT_EXCEL_NAME = DEFAULT_EXCEL_PATH.name
