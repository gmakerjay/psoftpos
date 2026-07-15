# -*- coding: utf-8 -*-
"""
USB Port Scanner & Printer Diagnostic
วนลูปเปลี่ยนพอร์ต USB ให้ XP-58 (copy 1) เพื่อค้นหาว่าสายจริงเสียบอยู่ช่องไหน
"""
import sys
import time
import win32print

# ข้อมูลจำลองสำหรับยิงทดสอบสั้นๆ
def get_receipt_data(port_name):
    return {
        'sale_number': f'PORT-{port_name}',
        'sale_date': '15/07/2026',
        'company': {
            'name': f'พอร์ต {port_name}',
            'address': f'ทดสอบพิมพ์ผ่านพอร์ต {port_name}',
            'phone': '081-234-5678',
            'tax_id': '1234567890123'
        },
        'items': [
            {'product_name': f'สแกนพอร์ต {port_name}', 'quantity': 1, 'unit_price': 100.0, 'total_price': 100.0}
        ],
        'total_amount': 100.0,
        'paid_amount': 100.0,
        'change_amount': 0.0,
        'cashier': 'สแกนเนอร์'
    }

def scan_usb_ports():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.printer_utils import PrinterManager
    
    printer_name = "XP-58 (copy 1)"
    usb_ports = ["USB001", "USB002", "USB003", "USB004", "USB005"]
    
    print(f"=== เริ่มต้นการสแกนหาพอร์ต USB สำหรับ {printer_name} ===")
    
    # ดึงค่าพอร์ตเดิมไว้คืนค่ากรณีจำเป็น
    original_port = None
    try:
        h_info = win32print.OpenPrinter(printer_name)
        p_info = win32print.GetPrinter(h_info, 2)
        original_port = p_info['pPortName']
        win32print.ClosePrinter(h_info)
        print(f"พอร์ตเดิมของเครื่องพิมพ์คือ: {original_port}")
    except Exception as e:
        print(f"ไม่สามารถตรวจสอบพอร์ตเริ่มต้นได้: {e}")
        return
        
    for port in usb_ports:
        print(f"\nกำลังทดสอบเชื่อมโยงเครื่องพิมพ์ไปที่พอร์ต: {port}...")
        
        # 1. เปลี่ยนพอร์ตของเครื่องพิมพ์ผ่าน Windows API
        try:
            hprinter = win32print.OpenPrinter(printer_name, {'DesiredAccess': win32print.PRINTER_ACCESS_ADMINISTER})
            p = win32print.GetPrinter(hprinter, 2)
            p['pPortName'] = port
            win32print.SetPrinter(hprinter, 2, p, 0)
            win32print.SetPrinter(hprinter, 0, None, win32print.PRINTER_CONTROL_PURGE) # เคลียร์คิวเดิม
            win32print.ClosePrinter(hprinter)
            print(f"  [SUCCESS] เปลี่ยนพอร์ตเป็น {port} และล้างคิวงานพิมพ์แล้ว")
        except Exception as e:
            print(f"  [FAILED] ไม่สามารถเปลี่ยนพอร์ตได้: {e}")
            continue
            
        # 2. ส่งงานพิมพ์ทดสอบผ่าน GDI
        try:
            pm = PrinterManager()
            pm.printer_name = printer_name
            pm.printer_type = "windows"
            pm.paper_size = "58mm"
            
            success = pm.print_receipt(get_receipt_data(port))
            print(f"  [SUCCESS] ส่งงานพิมพ์ทดสอบไปที่ {port} เรียบร้อย")
            
            # หน่วงเวลา 2 วินาทีเพื่อให้สพูลเลอร์ส่งงานพิมพ์
            time.sleep(2)
        except Exception as e:
            print(f"  [FAILED] ส่งงานพิมพ์ล้มเหลว: {e}")
            
    print("\n=== ส่งทดสอบครบทุกพอร์ต USB แล้ว ===")
    print("กรุณาดูว่ามีกระดาษพิมพ์ใบเสร็จไหลออกมาจากเครื่องพิมพ์ XP-58 หรือไม่")
    print("และหัวกระดาษระบุว่าเป็นพอร์ตใด (เช่น พอร์ต USB001, USB002...) เพื่อทำการล็อกพอร์ตนั้นครับ!")

if __name__ == "__main__":
    from pathlib import Path
    scan_usb_ports()
