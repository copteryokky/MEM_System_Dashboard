# config.py
from pathlib import Path

# โฟลเดอร์หลักของโปรเจกต์
BASE_DIR = Path(__file__).resolve().parent

# โฟลเดอร์เก็บไฟล์ข้อมูล
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ชื่อไฟล์ Excel กลาง (ให้ใช้ชื่อเดียวกับไฟล์จริง)
DEFAULT_EXCEL_NAME = "Smart.xlsx"
DEFAULT_EXCEL_PATH = DATA_DIR / DEFAULT_EXCEL_NAME


def get_excel_path():
    """
    คืนค่า Path ของไฟล์ Excel กลางที่ใช้ทั้ง APP หลักและหน้า QR
    ถ้าไม่มีไฟล์ จะคืน DEFAULT_EXCEL_PATH (แต่ caller ต้องตรวจเองว่ามีไฟล์ไหม)
    """
    return DEFAULT_EXCEL_PATH
