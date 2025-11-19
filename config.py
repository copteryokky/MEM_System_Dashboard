from pathlib import Path

# โฟลเดอร์หลักของโปรเจกต์
BASE_DIR = Path(__file__).resolve().parent

# โฟลเดอร์เก็บไฟล์ Excel
DATA_DIR = BASE_DIR / "data"

# ชื่อไฟล์เริ่มต้น (ถ้ามีไฟล์นี้อยู่จะใช้เป็นค่า default)
DEFAULT_EXCEL_NAME = "Smart Asset Lab New.xlsx"
DEFAULT_EXCEL_PATH = DATA_DIR / DEFAULT_EXCEL_NAME
