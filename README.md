# MEM System Dashboard (Streamlit)

ระบบบริหารจัดการครุภัณฑ์เครื่องมือแพทย์ (MEM System) เวอร์ชันตัวอย่าง

- Login พื้นฐาน (ผู้ใช้ `admin` / รหัสผ่าน `admin123`)
- หน้าแรก: dashboard แสดงสถานะครุภัณฑ์แบบกราฟ
- หน้ารายการครุภัณฑ์: แสดงตาราง, เลือกแถว, แก้ไขฟอร์ม และบันทึกกลับ Excel
- รองรับการอัปโหลดไฟล์ Excel ใหม่ (แทนที่ / เพิ่มตัวเลือกไฟล์)

## การติดตั้ง

```bash
pip install -r requirements.txt
```

## การรัน

```bash
streamlit run app.py
```

## โครงสร้างโฟลเดอร์

- `app.py`            : main app
- `auth.py`           : login
- `config.py`         : path / ตั้งค่าไฟล์ Excel
- `charts.py`         : ฟังก์ชันสร้างกราฟ Altair
- `data/`             : เก็บไฟล์ Excel
- `.streamlit/`       : theme
- `.gitignore`        : สำหรับ Git
