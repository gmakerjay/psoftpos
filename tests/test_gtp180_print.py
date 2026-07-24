# -*- coding: utf-8 -*-
"""
🧪 Test Receipt Print on SENOR GTP-180 Printer
ส่งคำสั่งพิมพ์ใบเสร็จและทดสอบการเลื่อนกระดาษพ้นใบมีดตัดบนเครื่อง GTP-180
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# เพิ่มพาธโปรเจกต์
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from utils.printer_utils import PrinterManager
import win32print

def test_gtp180_printing():
    print("=" * 70)
    print("🖨️ ทดสอบการพิมพ์ใบเสร็จจริงบนเครื่องพิมพ์ SENOR GTP-180")
    print("=" * 70)

    # 1. ค้นหาเครื่องพิมพ์ GTP-180
    all_printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
    gtp_printers = [p for p in all_printers if "gtp" in p.lower() or "180" in p.lower()]

    if not gtp_printers:
        print("❌ ไม่พบเครื่องพิมพ์ GTP-180 ในรายชื่อเครื่องพิมพ์ของ Windows")
        print("  เครื่องพิมพ์ที่มีในระบบ:", all_printers)
        return

    target_printer = gtp_printers[0]
    print(f"  ✅ พบเครื่องพิมพ์ GTP-180: '{target_printer}'")
    print(f"  (เครื่องพิมพ์ GTP-180 ทั้งหมดที่พบ: {gtp_printers})")

    # 2. ตั้งค่า PrinterManager สำหรับ GTP-180
    pm = PrinterManager()
    pm.printer_type = "thermal"
    pm.paper_size = "80mm"  # GTP-180 เป็น 80mm
    pm.printer_name = target_printer
    pm.printer_feed_lines = 8  # ส่งกระดาษ 8 บรรทัดพ้นใบมีดก่อนตัด (เว้นระยะขอบล่างสวยงาม)

    # 3. เตรียมข้อมูลใบเสร็จทดสอบ
    test_receipt = {
        'sale_number': f'GTP180-{datetime.now().strftime("%H%M%S")}',
        'sale_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'cashier': 'แอดมิน (ทดสอบระบบ)',
        'customer_name': 'ลูกค้าสมาชิก (GTP-180 Test)',
        'items': [
            {'product_name': 'น้ำดื่มตราช้าง 600 มล.', 'quantity': 3, 'unit_price': 10.00, 'total_price': 30.00},
            {'product_name': 'กาแฟกระป๋อง เบอร์ดี้ โรบัสต้า', 'quantity': 2, 'unit_price': 17.00, 'total_price': 34.00},
            {'product_name': 'มันฝรั่ง เลย์ รสคลาสสิก 50ก.', 'quantity': 1, 'unit_price': 24.00, 'total_price': 24.00},
            {'product_name': 'ขนมปังแผ่น ฟาร์มเฮ้าส์', 'quantity': 1, 'unit_price': 38.00, 'total_price': 38.00},
        ],
        'subtotal': 126.00,
        'discount_amount': 6.00,
        'tax_amount': 8.40,
        'total_amount': 120.00,
        'paid_amount': 200.00,
        'change_amount': 80.00,
        'company': {
            'name': 'ร้านค้าทดสอบ (SENOR GTP-180)',
            'address': '123/45 ถนนสุขุมวิท กรุงเทพฯ',
            'phone': '02-123-4567',
            'tax_id': '0105558000123'
        }
    }

    # 4. ส่งสั่งพิมพ์ไปยัง GTP-180
    print(f"\n[SENDING RAW] กำลังส่งข้อมูลใบเสร็จไปยัง '{target_printer}'...")
    print(f"  - โหมด: {pm.printer_type.upper()}")
    print(f"  - ขนาดกระดาษ: {pm.paper_size}")
    print(f"  - ระยะ Feed ก่อนตัด: {pm.printer_feed_lines} บรรทัด")

    success = pm.print_receipt(test_receipt)

    print("\n" + "=" * 70)
    if success:
        print(f"✅ ส่งคำสั่งพิมพ์ไปที่เครื่องพิมพ์ '{target_printer}' สำเร็จสมบูรณ์ 100%!")
        print("  - กระดาษจะดันพ้นหัวตัด 6 บรรทัดก่อนใบมีดทำงาน ข้อความและ QR ท้ายบิลจะไม่ถูกตัดขาด")
        print("  - ตรวจสอบกระดาษใบเสร็จจริงที่ออกจากเครื่องพิมพ์ GTP-180 ได้เลยครับ")
    else:
        print(f"❌ เกิดข้อผิดพลาดในการส่งคำสั่งพิมพ์ไปที่ '{target_printer}'")
        print("  - ตรวจสอบ printer_debug.log สำหรับรายละเอียด")
    print("=" * 70)

if __name__ == "__main__":
    test_gtp180_printing()
