# config.py
from pathlib import Path

# โฟลเดอร์หลักของโปรเจกต์ (ตำแหน่งเดียวกับไฟล์นี้)
BASE_DIR = Path(__file__).resolve().parent

# โฟลเดอร์เก็บไฟล์ Excel ทั้งหมด
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ชื่อไฟล์ Excel หลักที่ใช้ร่วมกันทุกหน้า
# ถ้าไฟล์จริงชื่ออื่น เช่น "Smart Asset Lab.xlsx" ให้แก้ตรงนี้ให้ตรง
DEFAULT_EXCEL_NAME = "Smart.xlsx"

# path เต็มของไฟล์ Excel หลัก
DEFAULT_EXCEL_PATH = DATA_DIR / DEFAULT_EXCEL_NAME


def get_excel_path() -> Path:
    """
    คืนค่า path ของไฟล์ Excel ที่ทุกหน้า (Dashboard + QR) ต้องใช้ร่วมกัน

    ลำดับการหาไฟล์:
    1) ใช้ data/Smart.xlsx ก่อน (DEFAULT_EXCEL_PATH)
    2) ถ้าไม่เจอ ให้เลือกไฟล์ .xls / .xlsx อันแรกในโฟลเดอร์ data
    3) ถ้ายังไม่เจอเลย ให้คืน DEFAULT_EXCEL_PATH (แต่จะอ่านไม่ได้
       จนกว่าจะสร้างไฟล์ Excel จริง ๆ)
    """
    # กรณีตั้งไฟล์หลักชื่อ Smart.xlsx และมีไฟล์อยู่แล้ว
    if DEFAULT_EXCEL_PATH.exists():
        return DEFAULT_EXCEL_PATH

    # ถ้ายังไม่มี Smart.xlsx แต่มีไฟล์ Excel อื่นใน data ก็ใช้ไฟล์แรก
    excel_files = sorted(DATA_DIR.glob("*.xls*"))
    if excel_files:
        return excel_files[0]

    # ถ้าไม่มีไฟล์ Excel เลย → คืน path ของ Smart.xlsx (เพื่อให้ error ชัดเจน)
    return DEFAULT_EXCEL_PATH
