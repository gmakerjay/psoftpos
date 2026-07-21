# -*- coding: utf-8 -*-
"""
A4 Barcode Label Sheet Simulation (30 Labels)
จำลองการสร้างไฟล์ PDF ป้ายสติ๊กเกอร์บาร์โค้ดขนาด A4 จำนวน 30 ดวง (3 คอลัมน์ x 10 แถว)
"""
import sys
from pathlib import Path
import os

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.pdf_utils import create_barcode_labels_pdf

def simulate_30_labels():
    print("=== เริ่มการจำลองการสร้างป้ายบาร์โค้ด 30 ดวงบน A4 ===")
    
    # จำลองสินค้าทดสอบ 1 รายการ สั่งพิมพ์จำนวน 30 ดวง (ดวงละ 1 ช่องสติกเกอร์)
    print_items = [
        {
            'product_name': 'กาแฟปรุงสำเร็จ ตรานกแก้ว คั่วกลางรสชาติเข้มข้น',
            'barcode': '885012345678',
            'retail_price': 25.00,
            'quantity': 30  # พิมพ์ 30 ดวง
        }
    ]
    
    out_pdf = Path("data/test_30_barcode_labels_A4.pdf")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    
    # เรียกใช้ฟังก์ชันสร้าง PDF ขนาด 3 คอลัมน์ x 10 แถว (30 ดวงพอดี 1 หน้า A4)
    success = create_barcode_labels_pdf(
        print_items, 
        str(out_pdf), 
        cols=3, 
        rows=10, 
        show_name=True, 
        show_price=True, 
        show_code=True
    )
    
    if success and out_pdf.exists():
        print(f"  [SUCCESS] สร้าง PDF สำเร็จแล้ว ขนาดไฟล์: {out_pdf.stat().st_size} bytes")
        print(f"  [INFO] กำลังเปิดไฟล์ PDF โชว์บนหน้าจอ: {out_pdf.name}")
        os.startfile(str(out_pdf.resolve()))
    else:
        print("  [ERROR] สร้าง PDF ล้มเหลว")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    simulate_30_labels()
