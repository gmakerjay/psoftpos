# -*- coding: utf-8 -*-
"""
การตั้งค่าโปรแกรมขายหน้าร้าน
"""

import os
import sys
from pathlib import Path

# เส้นทางหลัก - รองรับทั้ง development และ .exe
if getattr(sys, 'frozen', False):
    # ถ้าทำงานจาก .exe
    BASE_DIR = Path(os.path.dirname(sys.executable))
else:
    # ถ้าทำงานจาก Python ปกติ
    BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
BACKUP_DIR = DATA_DIR / "backups"
PRODUCTS_IMG_DIR = DATA_DIR / "products"

# สร้างโฟลเดอร์ที่จำเป็น
for directory in [DATA_DIR, BACKUP_DIR, PRODUCTS_IMG_DIR, ASSETS_DIR]:
    directory.mkdir(exist_ok=True)

# ฐานข้อมูล
DATABASE_PATH = DATA_DIR / "database.db"

# การตั้งค่า UI
APP_NAME = "โปรแกรมขายหน้าร้าน-PSoft"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1400x800"
MIN_WINDOW_SIZE = (1200, 700)

# ธีมสี (Modern Blue Theme)
COLORS = {
    "primary": "#1f538d",      # สีน้ำเงินเข้ม
    "secondary": "#2d7dd2",    # สีน้ำเงินสด
    "success": "#52c41a",      # สีเขียว
    "danger": "#ff4d4f",       # สีแดง
    "warning": "#faad14",      # สีส้ม
    "info": "#1890ff",         # สีฟ้า
    "light": "#f0f2f5",        # สีพื้นหลังอ่อน
    "dark": "#1a1a1a",         # สีดำ
    "white": "#ffffff",
    "text_dark": "#333333",
    "text_light": "#666666",
    "border": "#d9d9d9",
    "hover": "#40a9ff",
}

# การตั้งค่าฟอนต์
FONTS = {
    "title": ("Sarabun", 24, "bold"),
    "heading": ("Sarabun", 18, "bold"),
    "body": ("Sarabun", 14),
    "button": ("Sarabun", 14, "bold"),
    "small": ("Sarabun", 12),
}

# การตั้งค่าการขาย
SALE_SETTINGS = {
    "auto_print_receipt": True,
    "open_cash_drawer": True,
    "show_customer_display": False,
    "allow_negative_stock": False,
    "require_serial_number": False,
}

# ประเภทราคาขาย
PRICE_TYPES = {
    "retail": "ราคาปกติ",
    "wholesale": "ราคาส่ง",
    "special1": "ราคาพิเศษ 1",
    "special2": "ราคาพิเศษ 2 (ตัวแทนจำหน่าย)",
}

# ประเภทส่วนลด
DISCOUNT_TYPES = {
    "percent": "เปอร์เซ็นต์ (%)",
    "amount": "จำนวนเงิน (บาท)",
}

# การตั้งค่าบาร์โค้ด
BARCODE_SETTINGS = {
    "default_type": "code128",  # code128 หรือ ean13
    "include_text": True,
    "dpi": 300,
}

# การตั้งค่าการพิมพ์
PRINTER_SETTINGS = {
    "receipt_width": 80,  # มม.
    "paper_size": "A4",
    "margin_top": 10,
    "margin_bottom": 10,
    "margin_left": 5,
    "margin_right": 5,
}

# การตั้งค่าสต็อก
STOCK_SETTINGS = {
    "low_stock_threshold": 10,
    "enable_alerts": True,
    "auto_deduct": True,
}

# การตั้งค่าสำรองข้อมูล
BACKUP_SETTINGS = {
    "auto_backup": True,
    "backup_interval_days": 7,
    "max_backups": 10,
}

# สิทธิ์ผู้ใช้
USER_ROLES = {
    "admin": "ผู้ดูแลระบบ",
    "manager": "ผู้จัดการ",
    "cashier": "พนักงานขาย",
    "stock_manager": "พนักงานสต็อก",
}

# สิทธิ์การเข้าถึง
PERMISSIONS = {
    "admin": ["all"],
    "manager": [
        "view_dashboard",
        "manage_products",
        "manage_sales",
        "view_reports",
        "manage_stock",
        "manage_users",
        "view_history",
    ],
    "cashier": [
        "view_dashboard",
        "manage_sales",
        "view_products",
    ],
    "stock_manager": [
        "view_dashboard",
        "manage_products",
        "manage_stock",
        "view_reports",
    ],
}

# ภาษี
TAX_RATE = 0.07  # VAT 7%

# โหมดประสิทธิภาพ (สำหรับคอมรุ่นเก่า)
PERFORMANCE_MODE = {
    "enabled": True,  # เปิดโหมดประสิทธิภาพ
    "reduce_animations": True,  # ลด animation/effects
    "lazy_load_images": True,  # โหลดรูปแบบ lazy loading
    "pagination_enabled": True,  # เปิด pagination สำหรับรายการยาว
    "items_per_page": 30,  # จำนวนรายการต่อหน้า (ลดจาก 50 เพื่อประหยัด RAM)
    "max_cached_images": 20,  # จำนวนรูปสูงสุดใน cache (ลดจาก 30)
    "reduce_ui_refresh": True,  # ลดความถี่ของ UI refresh
    "disable_hover_effects": True,  # ปิด hover effects
    "compress_images": True,  # บีบอัดรูปภาพ
    "batch_widget_create": True,  # สร้าง widget แบบกลุ่ม ลด layout recalculation
}

# การตั้งค่าปรับปรุงรูปภาพ (สำหรับประสิทธิภาพ)
IMAGE_OPTIMIZATION = {
    "thumbnail_size": (40, 40),  # ขนาด thumbnail (ลดจาก 50x50)
    "max_image_size": (600, 600),  # ขนาดรูปสูงสุด (ลดจาก 800x800)
    "quality": 65,  # คุณภาพการบีบอัด (ลดจาก 75 เพื่อโหลดเร็วขึ้น)
    "format": "JPEG",  # รูปแบบไฟล์ (JPEG เบากว่า PNG)
    "resample_method": "BILINEAR",  # BILINEAR เร็วกว่า LANCZOS 3x
}

# ซิงค์การตั้งค่ากับ performance_config (หากมี)
try:
    import performance_config
    if hasattr(performance_config, 'LOW_END_MODE'):
        PERFORMANCE_MODE["enabled"] = performance_config.LOW_END_MODE
    if hasattr(performance_config, 'MAX_IMAGE_CACHE_SIZE'):
        PERFORMANCE_MODE["max_cached_images"] = performance_config.MAX_IMAGE_CACHE_SIZE
    if hasattr(performance_config, 'IMAGE_THUMBNAIL_SIZE'):
        IMAGE_OPTIMIZATION["thumbnail_size"] = performance_config.IMAGE_THUMBNAIL_SIZE
    if hasattr(performance_config, 'IMAGE_QUALITY'):
        IMAGE_OPTIMIZATION["quality"] = performance_config.IMAGE_QUALITY
except ImportError:
    pass


# ข้อมูลบริษัท (สำหรับใบเสร็จ)
COMPANY_INFO = {
    "name": "ชื่อร้านค้า",
    "address": "ที่อยู่ร้านค้า",
    "phone": "เบอร์โทรศัพท์",
    "tax_id": "เลขประจำตัวผู้เสียภาษี",
    "email": "contact@shop.com",
    "website": "www.shop.com",
    "branch": "สำนักงานใหญ่",
}

# รูปแบบวันที่และเวลา
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DB_DATE_FORMAT = "%Y-%m-%d"
DB_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ข้อความ
MESSAGES = {
    "login_success": "เข้าสู่ระบบสำเร็จ",
    "login_failed": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
    "save_success": "บันทึกข้อมูลสำเร็จ",
    "save_failed": "บันทึกข้อมูลไม่สำเร็จ",
    "delete_success": "ลบข้อมูลสำเร็จ",
    "delete_failed": "ลบข้อมูลไม่สำเร็จ",
    "confirm_delete": "ยืนยันการลบข้อมูล",
    "low_stock": "สินค้าในสต็อกเหลือน้อย",
    "out_of_stock": "สินค้าหมด",
    "sale_success": "ทำรายการขายสำเร็จ",
    "sale_failed": "ทำรายการขายไม่สำเร็จ",
    "return_success": "คืนสินค้าสำเร็จ",
    "return_failed": "คืนสินค้าไม่สำเร็จ",
}


def load_config_from_db():
    """ดึงข้อมูลการตั้งค่าจากฐานข้อมูลมาอัปเดตลงในตัวแปร TAX_RATE และ COMPANY_INFO"""
    import sqlite3
    global TAX_RATE, COMPANY_INFO
    try:
        # ตรวจสอบว่ามีไฟล์ฐานข้อมูลอยู่จริง
        db_path = str(DATABASE_PATH)
        if not os.path.exists(db_path):
            return
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # ตรวจสอบว่ามีตาราง settings ในฐานข้อมูล
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if not cursor.fetchone():
            conn.close()
            return
            
        cursor.execute("SELECT setting_key, setting_value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        
        settings = {row['setting_key']: row['setting_value'] for row in rows}
        
        # อัปเดต TAX_RATE
        if 'tax_rate' in settings:
            try:
                TAX_RATE = float(settings['tax_rate'])
            except ValueError:
                pass
                
        # อัปเดต COMPANY_INFO
        for key in COMPANY_INFO.keys():
            db_key = f"company_{key}"
            if db_key in settings:
                COMPANY_INFO[key] = settings[db_key]
                
    except Exception as e:
        print(f"Error loading config from database: {e}")

