# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.printer_utils import PrinterManager

pm = PrinterManager()
pm.paper_size = "80mm"

test_receipt = {
    'sale_number': 'SL20260724-VERIFY',
    'sale_date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    'cashier': 'แอดมิน',
    'customer_name': 'คุณสมชาย ใจดี',
    'items': [
        {'product_name': 'น้ำดื่มตราช้าง 600 มล.', 'quantity': 3, 'unit_price': 10.00, 'total_price': 30.00},
        {'product_name': 'กาแฟกระป๋อง เบอร์ดี้ โรบัสต้า', 'quantity': 2, 'unit_price': 17.00, 'total_price': 34.00},
        {'product_name': 'มันฝรั่ง เลย์ รสคลาสสิก 50ก.', 'quantity': 1, 'unit_price': 24.00, 'total_price': 24.00},
    ],
    'subtotal': 88.00,
    'discount_amount': 0.00,
    'tax_amount': 6.16,
    'total_amount': 88.00,
    'paid_amount': 100.00,
    'change_amount': 12.00,
    'company': {
        'name': 'ร้านค้าทดสอบ (SENOR GTP-180)',
        'address': '123/45 ถนนสุขุมวิท กรุงเทพฯ',
        'phone': '02-123-4567',
        'tax_id': '0105558000123'
    }
}

img = pm._render_receipt_image(test_receipt)
preview_path = BASE_DIR / "tests" / "receipt_preview.png"
img.save(preview_path)
print(f"Receipt image dimensions: {img.size[0]}x{img.size[1]} pixels")
print(f"Saved receipt preview to: {preview_path.resolve()}")
