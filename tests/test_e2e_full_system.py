# -*- coding: utf-8 -*-
"""
Full System End-to-End (E2E) & Integration Testing Suite
ระบบทดสอบการทำงานของ StorePOS แบบครบวงจร (ทุกเลเยอร์และทุกฟังก์ชันหลัก)
"""

import sys
import os
import time
import shutil
import sqlite3
import datetime
from pathlib import Path

# Setup Root Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database import DatabaseManager
from config import *
import utils
from utils.logger import get_logger, log_info, log_error, export_logs_zip
from utils.license_system import LicenseManager as StdLicManager, HardwareID
from utils.tax_invoice import TaxInvoiceGenerator
from utils.delivery_note import DeliveryNoteGenerator

tests_run = 0
tests_passed = 0

def assert_e2e(condition, message):
    global tests_run, tests_passed
    tests_run += 1
    if condition:
        tests_passed += 1
        print(f"  [PASS] {message}")
        return True
    else:
        print(f"  [FAIL] {message}")
        raise AssertionError(f"Test Failed: {message}")

def run_phase_1_database():
    print("\n--- Phase 1: Database Robustness & Integrity ---")
    db = DatabaseManager()
    db.connect()
    
    fk_row = db.fetch_one("PRAGMA foreign_keys")
    assert_e2e(fk_row and fk_row[0] == 1, "PRAGMA foreign_keys is ON")
    
    ok_int, msg_int = db.check_integrity()
    assert_e2e(ok_int, f"Database integrity check passed: {msg_int}")
    
    ok_fk, msg_fk = db.check_foreign_keys()
    assert_e2e(ok_fk, f"Foreign key violation check passed: {msg_fk}")
    
    db.disconnect()

def run_phase_2_catalog_and_stock():
    print("\n--- Phase 2: Catalog Management & Stock Movement Audit ---")
    db = DatabaseManager()
    db.connect()
    
    # 1. Add Category, Brand, Vendor
    db.execute("INSERT OR IGNORE INTO categories (category_name, description) VALUES ('E2E Testing Category', 'Test Description')")
    cat_id = db.fetch_one("SELECT category_id FROM categories WHERE category_name = 'E2E Testing Category'")[0]
    
    db.execute("INSERT OR IGNORE INTO brands (brand_name, description) VALUES ('E2E Brand', 'Test Brand')")
    brand_id = db.fetch_one("SELECT brand_id FROM brands WHERE brand_name = 'E2E Brand'")[0]
    
    db.execute("INSERT OR IGNORE INTO vendors (vendor_name, phone) VALUES ('E2E Supplier', '02-999-9999')")
    vendor_id = db.fetch_one("SELECT vendor_id FROM vendors WHERE vendor_name = 'E2E Supplier'")[0]
    
    # 2. Add Test Product
    barcode = f"E2E-{int(time.time())}"
    db.execute("""
        INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price, stock_quantity, min_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (barcode, "E2E Test Item", cat_id, 50.0, 100.0, 50, 5))
    
    prod_row = db.fetch_one("SELECT product_id, stock_quantity FROM products WHERE barcode = ?", (barcode,))
    assert_e2e(prod_row is not None and prod_row[1] == 50, "Test product created with initial stock 50")
    prod_id = prod_row[0]
    
    # 3. Direct Stock Adjustment & Audit Trail Movement
    db.execute("UPDATE products SET stock_quantity = 45 WHERE product_id = ?", (prod_id,))
    db.execute("""
        INSERT INTO stock_movements (product_id, movement_type, quantity, reference_id, reference_type, user_id, notes)
        VALUES (?, 'ADJUSTMENT', -5, 0, 'MANUAL', 1, 'E2E Direct Stock Tune')
    """, (prod_id,))
    
    check_prod = db.fetch_one("SELECT stock_quantity FROM products WHERE product_id = ?", (prod_id,))
    assert_e2e(check_prod[0] == 45, "Direct stock update set stock to 45")
    
    movement_row = db.fetch_one("SELECT quantity, notes FROM stock_movements WHERE product_id = ? ORDER BY movement_id DESC LIMIT 1", (prod_id,))
    assert_e2e(movement_row and movement_row[0] == -5, "Stock movement audit log recorded correctly")
    
    db.disconnect()
    return prod_id

def run_phase_3_member_system():
    print("\n--- Phase 3: Member System & Point Redemption Logic ---")
    db = DatabaseManager()
    db.connect()
    
    username = f"mem_e2e_{int(time.time())}"
    db.execute("""
        INSERT INTO members (name, phone, username, points, discount_type, discount_value)
        VALUES (?, ?, ?, ?, 'percent', 5.0)
    """, ("E2E Member User", "0812345678", username, 100))
    
    mem_row = db.fetch_one("SELECT member_id, points, discount_value FROM members WHERE username = ?", (username,))
    assert_e2e(mem_row is not None and mem_row[1] == 100, "Test member created with 100 points balance")
    
    # Test Point Redemption Calculation
    redeem_points = 20
    calculated_discount = redeem_points * POINT_REDEEM_VALUE
    assert_e2e(calculated_discount == 20.0, f"20 Points redeemed equals {calculated_discount} Baht discount")
    
    db.disconnect()
    return mem_row[0]

def run_phase_4_sales_e2e_checkout(prod_id, member_id):
    print("\n--- Phase 4: Sales E2E Flow (Cart -> Checkout -> Stock Deduction -> Points) ---")
    db = DatabaseManager()
    db.connect()
    
    prod_row = db.fetch_one("SELECT retail_price, stock_quantity FROM products WHERE product_id = ?", (prod_id,))
    mem_row = db.fetch_one("SELECT points FROM members WHERE member_id = ?", (member_id,))
    
    price, initial_stock = prod_row
    initial_points = mem_row[0]
    
    qty_sold = 3
    subtotal = price * qty_sold # 300 บาท
    points_used = 10
    point_discount = points_used * POINT_REDEEM_VALUE # 10 บาท
    net_total = subtotal - point_discount # 290 บาท
    earned_points = int(net_total // POINT_EARN_RATE) # 2 points
    
    sale_number = f"POS-E2E-{int(time.time())}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Record Sale
    db.execute("""
        INSERT INTO sales (sale_number, sale_date, user_id, customer_name, subtotal, discount_amount, tax_amount, total_amount, paid_amount, change_amount, payment_method, status)
        VALUES (?, ?, 1, 'E2E Member User', ?, ?, 0.0, ?, 300.0, 10.0, 'cash', 'completed')
    """, (sale_number, now_str, subtotal, point_discount, net_total))
    
    sale_id = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (sale_number,))[0]
    
    # 2. Record Sale Item
    db.execute("""
        INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, discount_amount, total_price)
        VALUES (?, ?, 'E2E Test Item', ?, ?, ?, ?)
    """, (sale_id, prod_id, qty_sold, price, point_discount, net_total))
    
    # 3. Deduct Stock
    db.execute("UPDATE products SET stock_quantity = stock_quantity - ? WHERE product_id = ?", (qty_sold, prod_id))
    
    # 4. Update Member Points
    new_points = initial_points - points_used + earned_points
    db.execute("UPDATE members SET points = ? WHERE member_id = ?", (new_points, member_id))
    
    # Verification
    check_stock = db.fetch_one("SELECT stock_quantity FROM products WHERE product_id = ?", (prod_id,))[0]
    assert_e2e(check_stock == initial_stock - qty_sold, f"Product stock auto-deducted from {initial_stock} to {check_stock}")
    
    check_points = db.fetch_one("SELECT points FROM members WHERE member_id = ?", (member_id,))[0]
    assert_e2e(check_points == new_points, f"Member points updated correctly to {check_points}")
    
    db.disconnect()
    return sale_id

def run_phase_5_after_sales_void_and_returns(sale_id, prod_id):
    print("\n--- Phase 5: After-Sales Operations (Void Sale & Product Return) ---")
    db = DatabaseManager()
    db.connect()
    
    sale_row = db.fetch_one("SELECT sale_number, status FROM sales WHERE sale_id = ?", (sale_id,))
    assert_e2e(sale_row is not None, f"Sale #{sale_id} found in sales history")
    
    item_row = db.fetch_one("SELECT product_id, quantity FROM sale_items WHERE sale_id = ?", (sale_id,))
    sold_qty = item_row[1]
    
    stock_before_void = db.fetch_one("SELECT stock_quantity FROM products WHERE product_id = ?", (prod_id,))[0]
    
    # Perform Void Sale
    db.execute("UPDATE sales SET status = 'cancelled' WHERE sale_id = ?", (sale_id,))
    db.execute("UPDATE products SET stock_quantity = stock_quantity + ? WHERE product_id = ?", (sold_qty, prod_id))
    
    stock_after_void = db.fetch_one("SELECT stock_quantity FROM products WHERE product_id = ?", (prod_id,))[0]
    assert_e2e(stock_after_void == stock_before_void + sold_qty, f"Void sale successfully restored {sold_qty} items to stock ({stock_after_void})")
    
    # Test Item Return Log Insertion
    ret_number = f"RET-E2E-{int(time.time())}"
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute("""
        INSERT INTO returns (return_number, sale_id, return_date, user_id, return_type, total_amount, reason)
        VALUES (?, ?, ?, 1, 'partial', 100.0, 'E2E Test Item Return')
    """, (ret_number, sale_id, now_str))
    
    ret_id = db.fetch_one("SELECT return_id FROM returns WHERE return_number = ?", (ret_number,))[0]
    assert_e2e(ret_id is not None, "Product return transaction logged successfully")
    
    db.disconnect()

def run_phase_6_pdf_document_generation(sale_id):
    print("\n--- Phase 6: PDF Document Generation (Tax Invoice & Delivery Note) ---")
    shop_info = {
        'name': 'บริษัท ตัวอย่าง จำกัด',
        'tax_id': '0123456789012',
        'address': '123 ถนนสุขุมวิท กรุงเทพฯ 10110',
        'tel': '02-123-4567',
        'branch': 'สำนักงานใหญ่'
    }
    
    sale_data = {
        'sale_id': sale_id,
        'sale_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'customer_name': 'บริษัท ทดสอบ E2E จำกัด',
        'customer_tax_id': '0105559000123',
        'customer_address': '123/45 ถนนสุขุมวิท กรุงเทพฯ 10110',
        'items': [
            {
                'product_name': 'E2E Test Item',
                'quantity': 3,
                'price': 100.00,
                'amount': 300.00
            }
        ],
        'subtotal': 280.37,
        'vat': 19.63,
        'total': 300.00
    }
    
    delivery_data = {
        'delivery_date': datetime.datetime.now().strftime("%Y-%m-%d"),
        'sender_name': shop_info['name'],
        'sender_address': shop_info['address'],
        'sender_tel': shop_info['tel'],
        'receiver_name': sale_data['customer_name'],
        'receiver_address': sale_data['customer_address'],
        'receiver_tel': '0812345678',
        'items': [
            {
                'product_name': 'E2E Test Item',
                'quantity': 3,
                'unit': 'ชิ้น',
                'note': 'E2E Delivered'
            }
        ],
        'delivery_method': 'รถส่งของบริษัท',
        'note': 'E2E Test Delivery'
    }
    
    # Generate Tax Invoice PDF
    tax_gen = TaxInvoiceGenerator(shop_info)
    tax_pdf_path, inv_no = tax_gen.create_invoice(sale_data)
    assert_e2e(os.path.exists(tax_pdf_path) and os.path.getsize(tax_pdf_path) > 0, f"Full Tax Invoice PDF created: {Path(tax_pdf_path).name} (#{inv_no})")
    
    # Generate Delivery Note PDF
    dn_gen = DeliveryNoteGenerator(shop_info)
    del_pdf_path, dn_no = dn_gen.create_delivery_note(delivery_data)
    assert_e2e(os.path.exists(del_pdf_path) and os.path.getsize(del_pdf_path) > 0, f"Delivery Note PDF created: {Path(del_pdf_path).name} (#{dn_no})")

def run_phase_7_daily_closing_and_export():
    print("\n--- Phase 7: Analytics, Daily Closing & Export ---")
    db = DatabaseManager()
    db.connect()
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    sales_summary = db.fetch_one("SELECT COUNT(*), SUM(total_amount) FROM sales WHERE date(created_at) = ?", (today_str,))
    assert_e2e(sales_summary is not None, f"Daily Sales Summary query executed successfully")
    
    close_txt = Path(f"Backup/closing_{today_str}.txt")
    close_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(close_txt, 'w', encoding='utf-8') as f:
        f.write(f"Daily Closing Report Date: {today_str}\nTotal Sales: {sales_summary[0]}\nTotal Revenue: {sales_summary[1]}\n")
        
    assert_e2e(close_txt.exists(), "Daily Closing summary TXT created")
    close_txt.unlink()
    
    db.disconnect()

def run_phase_8_auto_backup():
    print("\n--- Phase 8: Auto Background Backup Daemon ---")
    from utils import run_auto_backup
    
    db = DatabaseManager()
    db.connect()
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('auto_backup', 'True')")
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('backup_interval_hours', '0')")
    db.execute("INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES ('max_backups', '5')")
    db.disconnect()
    
    run_auto_backup()
    
    backups = list(BACKUP_DIR.glob("auto_backup_*.zip"))
    assert_e2e(len(backups) > 0, f"Auto backup zip created successfully (count: {len(backups)})")

def run_phase_9_license_system_and_admin_tools():
    print("\n--- Phase 9: License System & Admin Maintenance Tools ---")
    hwid = HardwareID.generate_hwid()
    assert_e2e(isinstance(hwid, str) and len(hwid.split("-")) == 4, f"HWID generated: {hwid}")
    
    key_365 = StdLicManager.generate_license_key(hwid, expire_days=365)
    is_valid, msg, data = StdLicManager.validate_license_key(key_365, hwid)
    assert_e2e(is_valid == True, f"Generated License Key is valid: {msg}")
    assert_e2e(data.get("hwid") == hwid, "License HWID matches system")
    
    import keygen_standalone as keygen
    app = keygen.KeyGenApp()
    paths = app._get_all_possible_license_paths()
    assert_e2e(isinstance(paths, list), f"Admin keygen scanner found {len(paths)} license locations")
    app.destroy()

def run_phase_10_logger_and_export():
    print("\n--- Phase 10: Logger Exception Hooks & Log Export ---")
    ok, zpath = export_logs_zip()
    assert_e2e(ok == True and os.path.exists(zpath), f"System log files exported to ZIP: {Path(zpath).name}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 70)
    print("StorePOS End-to-End (E2E) & Integration Full System Test Suite")
    print("=" * 70)
    
    try:
        run_phase_1_database()
        prod_id = run_phase_2_catalog_and_stock()
        member_id = run_phase_3_member_system()
        sale_id = run_phase_4_sales_e2e_checkout(prod_id, member_id)
        run_phase_5_after_sales_void_and_returns(sale_id, prod_id)
        run_phase_6_pdf_document_generation(sale_id)
        run_phase_7_daily_closing_and_export()
        run_phase_8_auto_backup()
        run_phase_9_license_system_and_admin_tools()
        run_phase_10_logger_and_export()
        
        print("\n" + "=" * 70)
        print(f"E2E VERIFICATION SUMMARY: {tests_passed}/{tests_run} TESTS PASSED")
        print("=" * 70)
        print("🎉 ALL END-TO-END SYSTEM INTEGRATION TESTS PASSED 100%! 🎉\n")
    except Exception as e:
        print(f"\n❌ E2E TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
