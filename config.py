# config.py
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_EXCEL_NAME = "Smart Asset Lab.xlsx"
DEFAULT_EXCEL_PATH = DATA_DIR / DEFAULT_EXCEL_NAME
