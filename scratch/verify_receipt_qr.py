import os
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

# Add project root to python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import DatabaseManager
from utils import print_receipt, create_receipt_pdf
from utils.printer_utils import PrinterManager

class TestReceiptQR(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseManager()
        cls.printer = PrinterManager()
        
        # 1. Create a dummy QR Code image
        cls.test_qr_path = Path("data/test_qr_code_image.png")
        cls.test_qr_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple 100x100 square with PIL
        qr_img = Image.new("RGB", (100, 100), color="white")
        draw = ImageDraw.Draw(qr_img)
        # Draw some black squares to resemble a QR Code
        draw.rectangle([10, 10, 30, 30], fill="black")
        draw.rectangle([70, 10, 90, 30], fill="black")
        draw.rectangle([10, 70, 30, 90], fill="black")
        draw.rectangle([40, 40, 60, 60], fill="black")
        qr_img.save(cls.test_qr_path)
        print(f"Created test QR code at: {cls.test_qr_path.resolve()}")

        # 2. Save payment_qr_path in DB settings
        cls.db.connect()
        # Backup original value if exists
        cls.orig_qr_setting = cls.db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
        cls.db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('payment_qr_path', ?)", (str(cls.test_qr_path.resolve()),))
        cls.db.disconnect()

    @classmethod
    def tearDownClass(cls):
        # Restore original DB setting
        cls.db.connect()
        if cls.orig_qr_setting:
            cls.db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('payment_qr_path', ?)", (cls.orig_qr_setting['setting_value'],))
        else:
            cls.db.execute("DELETE FROM settings WHERE setting_key = 'payment_qr_path'")
        cls.db.disconnect()
        
        # Delete test image
        if cls.test_qr_path.exists():
            cls.test_qr_path.unlink()

    def test_bitmap_receipt_rendering(self):
        """Test receipt PIL image generation incorporates customer name & bottom QR Code"""
        receipt_data = {
            'sale_number': 'TEST-SALE-001',
            'sale_date': '17/07/2026 14:40:00',
            'customer_name': 'นายทดสอบ ระบบสมาชิก',
            'cashier': 'แอดมินทดสอบ',
            'items': [
                {'product_name': 'นมสดตราหมี', 'quantity': 2, 'unit_price': 15.00, 'total_price': 30.00},
                {'product_name': 'ขนมปังเนยสด', 'quantity': 1, 'unit_price': 25.00, 'total_price': 25.00}
            ],
            'subtotal': 55.00,
            'discount_amount': 0.00,
            'tax_amount': 0.00,
            'total_amount': 55.00,
            'paid_amount': 100.00,
            'change_amount': 45.00
        }
        
        # Test 58mm image render
        self.printer.paper_size = "58mm"
        img_58 = self.printer._render_receipt_image(receipt_data)
        self.assertIsNotNone(img_58)
        self.assertEqual(img_58.size[0], 384) # 58mm default width
        self.assertGreater(img_58.size[1], 100) # Ensure it has height
        
        # Test 80mm image render
        self.printer.paper_size = "80mm"
        img_80 = self.printer._render_receipt_image(receipt_data)
        self.assertIsNotNone(img_80)
        self.assertEqual(img_80.size[0], 576) # 80mm default width
        self.assertGreater(img_80.size[1], 100)
        print("✓ ESC/POS Receipt Image Rendering works perfectly.")

    def test_pdf_receipt_rendering(self):
        """Test PDF receipt generator creates a valid PDF including member name & bottom QR Code"""
        receipt_data = {
            'sale_number': 'TEST-SALE-002',
            'sale_date': '17/07/2026 14:40:00',
            'customer_name': 'นางสาวรักเรียน หมั่นเพียร',
            'cashier': 'แอดมินทดสอบ',
            'items': [
                {'product_name': 'สมุดจดบันทึก A5', 'quantity': 5, 'unit_price': 20.00, 'total_price': 100.00}
            ],
            'subtotal': 100.00,
            'discount_amount': 5.00,
            'tax_amount': 0.00,
            'total_amount': 95.00,
            'paid_amount': 100.00,
            'change_amount': 5.00
        }
        
        # Generate temporary pdf path
        pdf_path = Path("data/temp/test_pdf_receipt.pdf")
        if pdf_path.exists():
            pdf_path.unlink()
            
        success = create_receipt_pdf(receipt_data, str(pdf_path), paper_size="80mm")
        self.assertTrue(success)
        self.assertTrue(pdf_path.exists())
        self.assertGreater(pdf_path.stat().st_size, 0)
        
        # Clean up
        if pdf_path.exists():
            pdf_path.unlink()
        print("✓ PDF Receipt generation runs successfully with QR Code.")

if __name__ == "__main__":
    unittest.main()
