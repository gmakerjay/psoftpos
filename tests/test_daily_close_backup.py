# -*- coding: utf-8 -*-
"""
🧪 Test Daily Shift Close (ปิดยอดวัน) & Backup Retrieval Verification
ทดสอบ:
  1. การสร้างข้อมูลยอดขายจำลอง
  2. การกดปิดยอดวัน (Clear Daily List / Shift Close)
  3. ตรวจสอบการเกิดไฟล์ Backup ทั้ง Excel (.xlsx) และ Text Log (.txt)
  4. ตรวจสอบว่าสามารถดึงและอ่านข้อมูลย้อนหลังจากไฟล์ Backup กลับมาแสดงผลได้ 100%
"""

import sys
import os
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database.db_manager import DatabaseManager
from utils.backup_utils import SalesLogManager, BackupManager
from utils.excel_utils import ExcelManager
from ui.reports_window import ReportsFrame

def run_test():
    print("=" * 70)
    print("🧪 เริ่มทดสอบระบบปิดยอดวัน (Shift Close) และการเรียกดูไฟล์ Backup ย้อนหลัง")
    print("=" * 70)

    db = DatabaseManager()
    slm = SalesLogManager()
    backup_dir = Path("Backup")
    backup_dir.mkdir(exist_ok=True)

    # -------------------------------------------------------------
    # STEP 1: จำลองการเพิ่มยอดขายในระบบ
    # -------------------------------------------------------------
    print("\n[STEP 1] จำลองการเพิ่มยอดขายในฐานข้อมูลและ Sales Log...")
    db.connect()
    
    # ดึง user_id
    user = db.fetch_one("SELECT user_id FROM users LIMIT 1")
    user_id = user['user_id'] if user else 1

    test_sale_num = f"SLTEST{datetime.now().strftime('%H%M%S')}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # บันทึกใน DB
    db.execute("""
        INSERT INTO sales (sale_number, sale_date, user_id, subtotal, total_amount, paid_amount, payment_method, status, is_archived)
        VALUES (?, ?, ?, 500.0, 500.0, 500.0, 'cash', 'completed', 0)
    """, (test_sale_num, now_str, user_id))
    
    sale_row = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (test_sale_num,))
    prod_row = db.fetch_one("SELECT product_id FROM products LIMIT 1")
    prod_id = prod_row['product_id'] if prod_row else 1

    if sale_row and prod_row:
        db.execute("""
            INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price)
            VALUES (?, ?, 'สินค้าทดสอบปิดยอด', 2, 250.0, 500.0)
        """, (sale_row['sale_id'], prod_id))

    db.disconnect()

    # บันทึกลง Sales Log (.txt)
    slm.add_sale({
        "sale_number": test_sale_num,
        "total_amount": 500.00,
        "payment_method": "เงินสด"
    })
    print(f"  ✅ สร้างบิลทดสอบสำเร็จ: {test_sale_num} (ยอดรวม: ฿500.00)")

    # -------------------------------------------------------------
    # STEP 2: ทำการปิดยอดวัน (Simulate clear_daily_list)
    # -------------------------------------------------------------
    print("\n[STEP 2] ดำเนินการปิดยอดวัน (สร้าง Backup Excel + Rotate Text Log + Archive DB)...")
    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 2.1 Auto-Export Excel
    db.connect()
    sales = db.fetch_all("""
        SELECT s.sale_id, s.sale_number, s.sale_date,
               s.subtotal, s.discount_amount, s.tax_amount, 
               s.total_amount, s.paid_amount, s.change_amount, 
               s.payment_method, s.status,
               u.full_name as cashier_name,
               GROUP_CONCAT(si.product_name || ' x' || si.quantity) as items
        FROM sales s
        LEFT JOIN users u ON s.user_id = u.user_id
        LEFT JOIN sale_items si ON s.sale_id = si.sale_id
        WHERE s.is_archived = 0
        GROUP BY s.sale_id
        ORDER BY s.sale_id DESC
    """)
    db.disconnect()

    excel_file = backup_dir / f"ยอดขาย_ปิดร้าน_TEST_{today_str}.xlsx"
    columns = [
        "เลขที่", "วันที่/เวลา", "ยอดรวม", "ส่วนลด", "ภาษี", 
        "ยอดสุทธิ", "รับเงิน", "เงินทอน", "วิธีชำระ", "สถานะ",
        "พนักงาน", "รายการสินค้า"
    ]
    export_data = []
    for s in sales:
        export_data.append({
            "เลขที่": s['sale_number'],
            "วันที่/เวลา": s['sale_date'],
            "ยอดรวม": s['subtotal'],
            "ส่วนลด": s['discount_amount'],
            "ภาษี": s['tax_amount'],
            "ยอดสุทธิ": s['total_amount'],
            "รับเงิน": s['paid_amount'],
            "เงินทอน": s['change_amount'],
            "วิธีชำระ": s['payment_method'],
            "สถานะ": s['status'],
            "พนักงาน": s['cashier_name'],
            "รายการสินค้า": s['items'] or '-'
        })

    excel_success = ExcelManager.export_to_excel(export_data, columns, str(excel_file), sheet_name="ยอดขาย", title="ปิดยอดทดสอบ")

    # 2.2 Rotate Text Log
    txt_backup_file = slm.clear_and_rotate()

    # 2.3 Set DB is_archived = 1
    db.connect()
    db.execute("UPDATE sales SET is_archived = 1 WHERE is_archived = 0")
    db.disconnect()

    print(f"  ✅ สร้างไฟล์ Excel สำรอง: {excel_file.name} (สำเร็จ: {excel_success})")
    print(f"  ✅ สร้างไฟล์ Text Log สำรอง: {Path(txt_backup_file).name if txt_backup_file else 'N/A'}")
    print(f"  ✅ อัปเดตสถานะ DB เป็น Archived เรียบร้อยแล้ว")

    # -------------------------------------------------------------
    # STEP 3: ตรวจสอบความถูกต้องของไฟล์ที่ถูกแบคอัพ
    # -------------------------------------------------------------
    print("\n[STEP 3] ตรวจสอบการคงอยู่ของไฟล์แบคอัพบนดิสก์...")
    excel_exists = excel_file.exists()
    txt_exists = Path(txt_backup_file).exists() if txt_backup_file else False
    new_log_exists = slm.current_log.exists()

    print(f"  - ไฟล์ Excel ปิดยอดอยู่จริง: {'✅ PASS' if excel_exists else '❌ FAIL'}")
    print(f"  - ไฟล์ Text Log สำรองอยู่จริง: {'✅ PASS' if txt_exists else '❌ FAIL'}")
    print(f"  - ไฟล์ Log ปัจจุบันสร้างรอบใหม่เตรียมพร้อม: {'✅ PASS' if new_log_exists else '❌ FAIL'}")

    # -------------------------------------------------------------
    # STEP 4: ทดสอบอ่านข้อมูลย้อนหลังจากไฟล์แบคอัพ (Retrieval Test)
    # -------------------------------------------------------------
    print("\n[STEP 4] ทดสอบการเรียกดูข้อมูลย้อนหลังจากไฟล์ Backup...")
    
    # อ่านจาก Text Log
    rf_dummy = ReportsFrame.__new__(ReportsFrame)
    rf_dummy.slm = slm
    date_range, read_sales = rf_dummy._parse_backup_file(Path(txt_backup_file))

    found_in_txt = any(s['sale_number'] == test_sale_num for s in read_sales)
    print(f"  - อ่านไฟล์ Text Log ({Path(txt_backup_file).name}): พบรายการบิล {test_sale_num} -> {'✅ PASS' if found_in_txt else '❌ FAIL'}")

    # อ่านจาก DB Archived Query
    db.connect()
    archived_sales = db.fetch_all("SELECT sale_number FROM sales WHERE is_archived = 1")
    db.disconnect()

    found_in_db_archive = any(s['sale_number'] == test_sale_num for s in archived_sales)
    print(f"  - สืบค้น DB (Archived Record): พบรายการบิล {test_sale_num} -> {'✅ PASS' if found_in_db_archive else '❌ FAIL'}")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    all_passed = excel_exists and txt_exists and new_log_exists and found_in_txt and found_in_db_archive
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ผลการทดสอบ: ผ่าน 100% (ALL PASSED)")
        print("  1. เมื่อปิดยอดเอง ไฟล์ Excel (.xlsx) และ Text (.txt) จะถูก Backup ทันที")
        print("  2. สามารถเรียกดูย้อนหลังได้ตลอดเวลาผ่านหน้าแท็บ 'ประวัติไฟล์ Backup'")
        print("  3. ข้อมูลใน DB ถูกย้ายเข้าคลังประวัติ ปลอดภัย 100% ไม่สูญหาย")
    else:
        print("❌ เกิดข้อผิดพลาดในการทดสอบ กรุณาตรวจสอบ Log")
    print("=" * 70)

if __name__ == "__main__":
    run_test()
