# -*- coding: utf-8 -*-
"""
Performance Optimization Config
ตั้งค่าเพื่อเพิ่มประสิทธิภาพสำหรับคอมพิวเตอร์รุ่นเก่า
"""

# Image Loading Optimization
MAX_IMAGE_CACHE_SIZE = 50  # จำนวนรูปภาพสูงสุดใน cache
IMAGE_THUMBNAIL_SIZE = (80, 80)  # ขนาด thumbnail มาตรฐาน
IMAGE_QUALITY = 85  # คุณภาพการบันทึกรูป (0-100)

# Database Optimization  
DB_CONNECTION_POOL_SIZE = 3  # จำนวน connection ใน pool
DB_QUERY_TIMEOUT = 10  # Timeout สำหรับ query (วินาที)
USE_CONNECTION_POOL = True  # เปิดใช้ connection pooling

# UI Optimization
LAZY_LOAD_TABS = True  # โหลดข้อมูล tab ตอนที่เปิด tab นั้น
VIRTUAL_SCROLLING_THRESHOLD = 50  # ถ้ามีรายการมากกว่านี้ใช้ virtual scrolling
DEBOUNCE_SEARCH_MS = 300  # หน่วงเวลาค้นหา (milliseconds)

# Product Cache
PRODUCTS_CACHE_SIZE = 500  # จำนวนสินค้าที่เก็บใน cache
PRODUCTS_CACHE_TTL = 300  # อายุ cache (วินาที)
CATEGORIES_CACHE_TTL = 600  # อายุ cache หมวดหมู่ (วินาที)

# Search Optimization
MAX_SEARCH_RESULTS = 30  # จำนวนผลลัพธ์ค้นหาสูงสุด
AUTOCOMPLETE_MIN_CHARS = 2  # ตัวอักษรขั้นต่ำสำหรับ autocomplete
AUTOCOMPLETE_MAX_RESULTS = 10  # จำนวนผลลัพธ์ autocomplete สูงสุด

# Chart/Graph Optimization
CHART_DPI = 80  # DPI สำหรับกราฟ (ยิ่งต่ำยิ่งเร็ว)
CHART_FIGURE_SIZE = (8, 5)  # ขนาดกราฟ (นิ้ว)
MAX_CHART_DATAPOINTS = 100  # จุดข้อมูลสูงสุดในกราฟ

# Memory Management
ENABLE_GARBAGE_COLLECTION = True  # เปิดใช้ garbage collection
GC_INTERVAL_MINUTES = 5  # รัน garbage collection ทุกกี่นาที
CLEAR_CACHE_ON_LOW_MEMORY = True  # ล้าง cache เมื่อ memory ต่ำ

# Performance Mode (สำหรับคอมรุ่นเก่า)
LOW_END_MODE = True  # เปิดโหมดประหยัดทรัพยากร
if LOW_END_MODE:
    MAX_IMAGE_CACHE_SIZE = 20
    DB_CONNECTION_POOL_SIZE = 2
    VIRTUAL_SCROLLING_THRESHOLD = 30
    CHART_DPI = 60
    PRODUCTS_CACHE_SIZE = 200

# Keyboard Shortcuts (Actual Implementation)
SHORTCUTS = {
    'POS (หน้าขายสินค้า)': {
        'F1': 'โฟกัสช่องค้นหา/ยิงบาร์โค้ด',
        'F7': 'ใส่ส่วนลด',
        'F8': 'เปิด/ปิด และกรอกภาษี VAT',
        'F9': 'เปิดหน้าขายใหม่ (Multi-Session)',
        'F10': 'ชำระเงิน',
        'F11': 'ล้างตะกร้า (ยกเลิกการขาย)',
        'F12': 'ปิดหน้าขายปัจจุบัน',
    },
    'Product Management (หน้าจัดการสินค้า)': {
        'F5 / Ctrl+N': 'เพิ่มสินค้าใหม่ (Wizard)',
        'Ctrl+F': 'ค้นหาสินค้า',
        'Ctrl+R': 'โหลด/รีเฟรชข้อมูลสินค้า',
    }
}

# Smart Features
ENABLE_AUTO_BACKUP = True  # สำรองข้อมูลอัตโนมัติ
AUTO_BACKUP_INTERVAL_HOURS = 24  # สำรองทุกกี่ชั่วโมง
ENABLE_SMART_SUGGESTIONS = True  # แนะนำสินค้าที่เกี่ยวข้อง
ENABLE_LOW_STOCK_ALERTS = True  # แจ้งเตือนสต็อกต่ำ
LOW_STOCK_THRESHOLD_DAYS = 7  # แจ้งเตือนเมื่อสต็อกใกล้หมดใน X วัน

print(f"Performance Mode: {'LOW-END' if LOW_END_MODE else 'NORMAL'}")
print(f"Image Cache: {MAX_IMAGE_CACHE_SIZE} images")
print(f"DB Pool Size: {DB_CONNECTION_POOL_SIZE} connections")
print(f"Chart Quality: {CHART_DPI} DPI")
