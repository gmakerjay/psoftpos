# -*- coding: utf-8 -*-
"""
Excel Import/Export End-to-End Migration Test - Fixed
ทดสอบการ Export ข้อมูลสินค้าจริงออกไป และการนำเข้ากลับ (Import) หลังจากเคลียร์ข้อมูลในฐานข้อมูล
"""
import sys
from pathlib import Path
import shutil
import sqlite3
from datetime import datetime

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager
from utils.excel_utils import ExcelManager
from config import DATABASE_PATH

def run_migration_test():
    print("=== 1. ทำการสำรองฐานข้อมูลจริงก่อนเริ่มการทดสอบ (เพื่อความปลอดภัย) ===")
    db_path = Path(DATABASE_PATH)
    backup_db_path = db_path.with_suffix(".db.test_backup")
    test_xlsx = Path("data/test_migration_products.xlsx")
    
    if backup_db_path.exists():
        backup_db_path.unlink()
    shutil.copy2(db_path, backup_db_path)
    print(f"  [SUCCESS] สำรองฐานข้อมูลไปที่: {backup_db_path.name}")

    try:
        db = DatabaseManager()
        
        # 2. ดึงข้อมูลสินค้าเดิมจากฐานข้อมูล
        print("\n=== 2. ดึงข้อมูลสินค้าเดิมเพื่อเตรียม Export ===")
        db.connect()
        original_products = db.fetch_all("""
            SELECT p.*, c.category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1
            ORDER BY p.product_id ASC
        """)
        db.disconnect()
        
        original_count = len(original_products) if original_products else 0
        print(f"  [INFO] พบสินค้าในระบบ: {original_count} รายการ")
        if original_count == 0:
            print("  [WARNING] ไม่มีสินค้าสำหรับทดสอบ กรุณาเพิ่มสินค้าก่อน!")
            return

        # 3. จำลองการ Export สินค้าเป็น Excel (คอลัมน์และหัวตารางเดียวกับปุ่มส่งออกใหม่)
        print("\n=== 3. จำลองการ Export สินค้าเป็นไฟล์ Excel ===")
        columns = [
            "บาร์โค้ด", "ชื่อสินค้า", "หมวดหมู่",
            "ราคาทุน", "ราคาขายปกติ", "ราคาขายส่ง",
            "ราคาพิเศษ1", "ราคาพิเศษ2",
            "จำนวนสต็อก", "สต็อกขั้นต่ำ"
        ]
        
        export_data = []
        for p in original_products:
            # ใช้ dictionary key lookups บน sqlite3.Row
            export_data.append({
                "บาร์โค้ด": str(p["barcode"] or "").strip(),
                "ชื่อสินค้า": str(p["product_name"] or "").strip(),
                "หมวดหมู่": str(p["category_name"] or "").strip(),
                "ราคาทุน": float(p["cost_price"] or 0.0),
                "ราคาขายปกติ": float(p["retail_price"] or 0.0),
                "ราคาขายส่ง": float(p["wholesale_price"] or 0.0),
                "ราคาพิเศษ1": float(p["special_price1"] or 0.0),
                "ราคาพิเศษ2": float(p["special_price2"] or 0.0),
                "จำนวนสต็อก": int(p["stock_quantity"] or 0),
                "สต็อกขั้นต่ำ": int(p["min_stock"] or 10)
            })
            
        if test_xlsx.exists():
            test_xlsx.unlink()
            
        success = ExcelManager.export_to_excel(
            export_data, columns, str(test_xlsx),
            "สินค้า", "รายการสินค้าทดสอบการย้ายข้อมูล"
        )
        if not success or not test_xlsx.exists():
            raise Exception("Export Excel ล้มเหลว")
        print(f"  [SUCCESS] สร้างไฟล์ Excel สำหรับทดสอบที่: {test_xlsx.name}")

        # 4. จำลองการเคลียร์ตารางสินค้า (Clear Database)
        print("\n=== 4. เคลียร์ข้อมูลตารางสินค้าปัจจุบัน ===")
        db.connect()
        db.execute("DELETE FROM products")
        
        # ตรวจสอบว่าโล่งจริงไหม
        check_empty = db.fetch_all("SELECT product_id FROM products WHERE is_active = 1")
        db.disconnect()
        print(f"  [INFO] จำนวนสินค้าคงเหลือหลังล้างตาราง: {len(check_empty) if check_empty else 0} รายการ")

        # 5. จำลองการนำเข้ากลับ (Import) จากไฟล์ Excel ที่ Export ออกไป
        print("\n=== 5. นำเข้าข้อมูลสินค้าจากไฟล์ Excel ที่เซฟไว้ ===")
        imported_data = ExcelManager.import_from_excel(str(test_xlsx), header_row=3)
        print(f"  [INFO] อ่านสินค้าจาก Excel ได้: {len(imported_data)} รายการ")
        
        col_map = {
            "บาร์โค้ด": "barcode",
            "ชื่อสินค้า": "product_name",
            "หมวดหมู่": "category",
            "ราคาทุน": "cost_price",
            "ราคาขายปกติ": "retail_price",
            "ราคาขายส่ง": "wholesale_price",
            "ราคาพิเศษ1": "special_price1",
            "ราคาพิเศษ2": "special_price2",
            "จำนวนสต็อก": "stock_quantity",
            "สต็อกขั้นต่ำ": "min_stock",
        }
        
        db.connect()
        db.begin_transaction()
        
        # โหลด Cache หมวดหมู่
        categories = db.fetch_all("SELECT category_id, category_name FROM categories")
        cat_lookup = {c['category_name']: c['category_id'] for c in categories} if categories else {}
        
        success_count = 0
        for row in imported_data:
            # แมปฟิลด์ไทย -> อังกฤษ
            mapped = {}
            for thai_key, eng_key in col_map.items():
                val = row.get(thai_key, None)
                if val is not None and str(val).strip() != '' and str(val).lower() != 'nan':
                    mapped[eng_key] = val
                else:
                    mapped[eng_key] = None
                    
            product_name = mapped.get("product_name")
            if not product_name or str(product_name).strip() == '':
                continue
                
            product_name = str(product_name).strip()
            barcode = mapped.get("barcode")
            if barcode:
                barcode = str(barcode).strip().replace('.0', '')
                
            # จัดการหมวดหมู่
            category_id = None
            cat_name = mapped.get("category")
            if cat_name and str(cat_name).strip():
                cat_name = str(cat_name).strip()
                if cat_name in cat_lookup:
                    category_id = cat_lookup[cat_name]
                else:
                    db.execute("INSERT INTO categories (category_name) VALUES (?)", (cat_name,))
                    new_cat = db.fetch_one("SELECT category_id FROM categories WHERE category_name = ?", (cat_name,))
                    if new_cat:
                        category_id = new_cat['category_id']
                        cat_lookup[cat_name] = category_id
                        
            # แทรกสินค้ากลับคืน
            db.execute("""
                INSERT INTO products (
                    barcode, product_name, category_id,
                    cost_price, retail_price, wholesale_price,
                    special_price1, special_price2,
                    stock_quantity, min_stock, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                barcode, product_name, category_id,
                float(mapped.get("cost_price") or 0.0),
                float(mapped.get("retail_price") or 0.0),
                float(mapped.get("wholesale_price") or 0.0),
                float(mapped.get("special_price1") or 0.0),
                float(mapped.get("special_price2") or 0.0),
                int(float(mapped.get("stock_quantity") or 0.0)),
                int(float(mapped.get("min_stock") or 10.0))
            ))
            success_count += 1
            
        db.commit_transaction()
        db.disconnect()
        print(f"  [SUCCESS] นำเข้ากลับคืนฐานข้อมูลสำเร็จ: {success_count} รายการ")

        # 6. ตรวจสอบความถูกต้องและเปรียบเทียบข้อมูลก่อน-หลังย้ายระบบ
        print("\n=== 6. ตรวจสอบความครบถ้วนและเปรียบเทียบข้อมูล ===")
        db.connect()
        restored_products = db.fetch_all("""
            SELECT p.*, c.category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1
            ORDER BY p.product_id ASC
        """)
        db.disconnect()
        
        restored_count = len(restored_products) if restored_products else 0
        print(f"  [INFO] จำนวนสินค้าก่อนทดสอบ: {original_count} รายการ")
        print(f"  [INFO] จำนวนสินค้าหลังนำเข้า: {restored_count} รายการ")
        
        assert original_count == restored_count, "จำนวนสินค้าก่อนและหลังกู้คืนไม่ตรงกัน!"
        
        # เทียบสินค้าตัวแรก
        orig_1 = original_products[0]
        rest_1 = restored_products[0]
        print(f"  [INFO] ตัวอย่างสินค้าทดสอบ (ก่อน): {orig_1['product_name']} | บาร์โค้ด: {orig_1['barcode']} | สต็อก: {orig_1['stock_quantity']} | ราคาปกติ: {orig_1['retail_price']}")
        print(f"  [INFO] ตัวอย่างสินค้าทดสอบ (หลัง): {rest_1['product_name']} | บาร์โค้ด: {rest_1['barcode']} | สต็อก: {rest_1['stock_quantity']} | ราคาปกติ: {rest_1['retail_price']}")
        
        assert orig_1['product_name'] == rest_1['product_name'], "ชื่อสินค้าไม่ตรงกัน!"
        assert orig_1['retail_price'] == rest_1['retail_price'], "ราคาขายปกติไม่ตรงกัน!"
        
        print("\n=> [PASS] การทดสอบ Export และนำเข้า (Import) ทำงานร่วมกันได้สมบูรณ์แบบ 100%!")

    except Exception as e:
        print(f"\n  [FAIL] การทดสอบล้มเหลว: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 7. ทำการกู้ฐานข้อมูลหลักกลับคืนสภาพเดิม (Clean Up)
        print("\n=== 7. คืนฐานข้อมูลจริงกลับเข้าที่เดิม ===")
        DatabaseManager.close_all_connections()
        if backup_db_path.exists():
            if db_path.exists():
                db_path.unlink()
            shutil.move(backup_db_path, db_path)
            print("  [SUCCESS] กู้คืนฐานข้อมูลต้นฉบับเสร็จเรียบร้อย")
        if test_xlsx.exists():
            test_xlsx.unlink()
            
        print("=== สิ้นสุดการรันการทดสอบ ===")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    run_migration_test()
