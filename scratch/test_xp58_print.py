# -*- coding: utf-8 -*-
"""
XP-58 Printer Diagnostic Tool
ยิงทดสอบการพิมพ์ภาษาไทยไปยังเครื่องพิมพ์ XP-58 โดยตรง
"""
import sys
from pathlib import Path

# แทรก path ของโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ข้อมูลทดสอบใบเสร็จภาษาไทย
receipt_data = {
    'sale_number': 'TEST-XP58',
    'sale_date': '15/07/2026 14:50:00',
    'company': {
        'name': 'ทดสอบ XP-58 ภาษาไทย',
        'address': 'ร้านตัวอย่าง ภาษาไทย 100% สระอู สระอุ สระอี สระอือ โดนจับสระและวรรณยุกต์ซ้อน',
        'phone': '081-234-5678',
        'tax_id': '1234567890123'
    },
    'items': [
        {'product_name': 'น้ำมันพืช ทิพ', 'quantity': 1, 'unit_price': 55.00, 'total_price': 55.00},
        {'product_name': 'ข้าวสาร หอมมะลิ', 'quantity': 2, 'unit_price': 180.00, 'total_price': 360.00},
        {'product_name': 'น้ำดื่ม ตราสิงห์', 'quantity': 12, 'unit_price': 10.00, 'total_price': 120.00},
    ],
    'total_amount': 535.00,
    'paid_amount': 600.00,
    'change_amount': 65.00,
    'cashier': 'แอดมิน'
}

def test_print_gdi():
    print("ส่งทดสอบแบบที่ 1: Windows GDI (พิมพ์ผ่านกราฟิกไดรเวอร์ใช้ฟอนต์ Tahoma)...")
    try:
        from utils.printer_utils import PrinterManager
        pm = PrinterManager()
        pm.printer_name = "XP-58"
        pm.printer_type = "windows"
        pm.paper_size = "58mm"
        
        success = pm.print_receipt(receipt_data)
        print("  ผลลัพธ์:", "สำเร็จ" if success else "ล้มเหลว")
    except Exception as e:
        print("  [ERROR] GDI Print failed:", e)

def test_print_escpos_26():
    print("ส่งทดสอบแบบที่ 2: Direct ESC/POS (รหัส CP874 - โค้ดเพจ 26)...")
    try:
        from utils.printer_utils import PrinterManager
        pm = PrinterManager()
        pm.printer_name = "XP-58"
        pm.printer_type = "thermal"
        pm.paper_size = "58mm"
        
        # เขียนคำสั่งทับค่าใน method
        ESC = b'\x1b'
        FS = b'\x1c'
        GS = b'\x1d'
        
        # สร้างคำสั่งแบบดั้งเดิมที่ล้างค่าสองไบต์ และใช้ Code Page 26
        commands = [
            ESC + b'@',            # Reset
            FS + b'.',             # Cancel Chinese
            ESC + b't\x1a',        # Code page 26 (Thai CP874)
            ESC + b'R\x00',        # USA Charset
        ]
        
        # สร้างส่วนเนื้อหาใบเสร็จปกติ
        raw_receipt = pm.generate_escpos_commands(receipt_data)
        # ตัดชุดคำสั่ง init 10 ไบต์แรกของ generate_escpos_commands ออกเพื่อเปลี่ยนหัวคำสั่งเอง
        header = b"".join(commands)
        final_job = header + raw_receipt[10:]
        
        success = pm.send_raw_to_printer(final_job)
        print("  ผลลัพธ์:", "สำเร็จ" if success else "ล้มเหลว")
    except Exception as e:
        print("  [ERROR] ESC/POS CP26 failed:", e)

def test_print_escpos_18():
    print("ส่งทดสอบแบบที่ 3: Direct ESC/POS (รหัส CP874 - โค้ดเพจ 18)...")
    try:
        from utils.printer_utils import PrinterManager
        pm = PrinterManager()
        pm.printer_name = "XP-58"
        pm.printer_type = "thermal"
        pm.paper_size = "58mm"
        
        ESC = b'\x1b'
        FS = b'\x1c'
        GS = b'\x1d'
        
        # เปลี่ยนใช้ Code page 18 (Thai อีกมาตรฐานหนึ่งของบางรุ่นเครื่องจีน)
        commands = [
            ESC + b'@',            # Reset
            FS + b'.',             # Cancel Chinese
            ESC + b't\x12',        # Code page 18 (Decimal 18 / Hex 12)
            ESC + b'R\x00',        # USA Charset
        ]
        
        raw_receipt = pm.generate_escpos_commands(receipt_data)
        header = b"".join(commands)
        final_job = header + raw_receipt[10:]
        
        success = pm.send_raw_to_printer(final_job)
        print("  ผลลัพธ์:", "สำเร็จ" if success else "ล้มเหลว")
    except Exception as e:
        print("  [ERROR] ESC/POS CP18 failed:", e)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print(" เริ่มส่งคำสั่งทดสอบพิมพ์ภาษาไทยไปยังเครื่องพิมพ์ XP-58")
    print("=" * 60)
    
    test_print_gdi()
    test_print_escpos_26()
    test_print_escpos_18()
    
    print("\nส่งคำสั่งทดสอบครบ 3 แบบแล้ว กรุณาตรวจสอบกระดาษที่ออกจากเครื่องพิมพ์ XP-58 ครับ!")
