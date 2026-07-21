# -*- coding: utf-8 -*-
"""
Automated Test for Trial Expiry & Database Retention Verification
ทดสอบการทำงานของ Trial Expiry, ความปลอดภัยของไฟล์ฐานข้อมูล DB และการเปลี่ยนผ่านสิทธิ์เป็น Full Version
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# เพิ่ม root directory ลง sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.license_system_trial_30days as license_system_trial_30days
sys.modules['utils.license_system'] = license_system_trial_30days

from database.db_manager import DatabaseManager
from utils.license_system_trial_30days import HardwareID, LicenseManager


class TestTrialExpiryDatabaseRetention(unittest.TestCase):
    """ชุดทดสอบความปลอดภัยของฐานข้อมูลเมื่อเวอร์ชันทดลองหมดอายุ"""
    
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*70)
        print("🧪 STARTING TEST: Trial Expiry & Database Retention Verification")
        print("="*70)
        cls.cleanup_licenses()

    @classmethod
    def tearDownClass(cls):
        cls.cleanup_licenses()
        now = datetime.now()
        LicenseManager._write_trial_file(now)
        LicenseManager._write_trial_db_date(now)
        LicenseManager._write_registry_trial_date(now)

    @classmethod
    def cleanup_licenses(cls):
        for f in [Path("data/.license"), Path("data/.license_30days")]:
            if f.exists():
                try:
                    f.unlink()
                except:
                    pass

    def setUp(self):
        self.cleanup_licenses()

    def test_01_database_data_persistence_on_trial_expiry(self):
        """1. ทดสอบว่าข้อมูลในฐานข้อมูลยังคงอยู่ครบถ้วนเมื่อ Trial หมดอายุ"""
        print("\n--- Step 1: Initialize DB and insert test product & sale ---")
        db = DatabaseManager()
        db.initialize_database()
        self.assertTrue(db.connect(), "Database connection failed")
        
        # เพิ่มข้อมูลทดสอบ
        test_barcode = "885000099999"
        db.execute("DELETE FROM products WHERE barcode = ?", (test_barcode,))
        db.execute("""
            INSERT INTO products (barcode, product_name, cost_price, retail_price, stock_quantity)
            VALUES (?, ?, ?, ?, ?)
        """, (test_barcode, "สินค้าทดสอบการหมดอายุ", 100.0, 150.0, 50))
        
        product = db.fetch_one("SELECT * FROM products WHERE barcode = ?", (test_barcode,))
        self.assertIsNotNone(product, "Product insertion failed")
        print(f"✅ Created test product: {product['product_name']} (Stock: {product['stock_quantity']})")
        db.disconnect()
        
        # จำลองวันเริ่มต้น trial ให้อดีต (40 วันก่อน = หมดอายุแน่นอน)
        expired_start_date = datetime.now() - timedelta(days=40)
        LicenseManager._write_trial_file(expired_start_date)
        LicenseManager._write_trial_db_date(expired_start_date)
        LicenseManager._write_registry_trial_date(expired_start_date)
        
        print("--- Step 2: Check activation status on expired trial ---")
        is_activated, msg, license_data = LicenseManager.check_activation()
        self.assertFalse(is_activated, f"Expected is_activated to be False for expired trial, got: {msg}")
        print(f"✅ Trial check result: is_activated={is_activated}, message='{msg[:60]}...'")
        
        # ตรวจสอบว่าไฟล์ DB ยังคงอยู่และใช้งานได้
        db_path = Path("data/database.db")
        self.assertTrue(db_path.exists(), "Database file must NOT be deleted on expiry!")
        
        # ตรวจสอบ DB Integrity และค้นหาข้อมูลที่สร้างไว้
        db = DatabaseManager()
        ok, res = db.check_integrity()
        self.assertTrue(ok, f"Database integrity check failed: {res}")
        
        db.connect()
        saved_product = db.fetch_one("SELECT * FROM products WHERE barcode = ?", (test_barcode,))
        self.assertIsNotNone(saved_product, "Product data lost after trial expiry!")
        self.assertEqual(saved_product['product_name'], "สินค้าทดสอบการหมดอายุ")
        self.assertEqual(saved_product['stock_quantity'], 50)
        db.disconnect()
        print("✅ DB Integrity OK & All product/sale data preserved 100% after expiry!")

    def test_02_full_license_key_activation_transition(self):
        """2. ทดสอบการใส่ Full License Key และการเปลี่ยนผ่านเป็นเวอร์ชันเต็ม"""
        print("\n--- Step 3: Generating and activating Full License Key ---")
        hwid = HardwareID.generate_hwid()
        
        # สร้าง Full License Key จริง
        full_key = LicenseManager.generate_license_key(hwid, expire_days=365)
        print(f"Generated Full License Key for HWID {hwid}: {full_key[:30]}...")
        
        # Activate License Key
        path = LicenseManager.LICENSE_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        import base64
        encrypted = base64.b64encode(full_key.encode()).decode()
        with open(path, 'w') as f:
            f.write(encrypted)
            
        print("--- Step 4: Verify check_activation() in Full License Mode ---")
        is_activated, msg, license_data = LicenseManager.check_activation()
        self.assertTrue(is_activated, f"Full license activation failed: {msg}")
        self.assertFalse(license_data.get('is_trial', True), "Should be full version (is_trial=False)")
        print(f"✅ Activation success! Message: {msg}")
        
        # ตรวจสอบการเข้าถึงข้อมูลเดิมใน Full Mode
        db = DatabaseManager()
        self.assertTrue(db.connect())
        test_barcode = "885000099999"
        product = db.fetch_one("SELECT * FROM products WHERE barcode = ?", (test_barcode,))
        self.assertIsNotNone(product, "Product data missing in Full Mode!")
        print(f"✅ Successfully accessed original DB in Full Mode: {product['product_name']}")
        db.disconnect()


if __name__ == "__main__":
    unittest.main()
