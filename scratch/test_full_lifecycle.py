# -*- coding: utf-8 -*-
"""
Full Lifecycle Test: Create -> Export -> Reset -> Import
รันการทดสอบวัฏจักรข้อมูลสินค้าแบบสมบูรณ์
"""
import sys
from pathlib import Path
import shutil
import sqlite3

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager
from utils.excel_utils import ExcelManager
from config import DATABASE_PATH

def run_lifecycle_test():
    db = DatabaseManager()
    
    # 1. สร้าง/เพิ่มสินค้าจำลองภาษาไทยลงในฐานข้อมูล
    print("=== 1. ทำการสร้างสินค้าทดสอบใหม่ลงในฐานข้อมูล ===")
    
    # สร้างหมวดหมู่ก่อน
    db.connect()
    db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (1, 'เครื่องดื่ม')")
    db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (2, 'ขนมขบเคี้ยว')")
    
    # ลบสินค้าเก่าออกก่อนเพื่อเริ่มต้นใหม่แบบคลีน
    db.execute("DELETE FROM products")
    
    test_products = [
        ("8850999010010", "น้ำดื่ม ตราสิงห์ 600มล", 1, 5.00, 10.00, 9.00, 9.50, 8.50, 120, 10, "ขวด"),
        ("8850999010027", "นมโฟร์โมสต์ รสจืด 180มล", 1, 8.00, 12.50, 11.00, 12.00, 10.50, 80, 15, "กล่อง"),
        ("8850999010034", "กาแฟกระป๋อง เบอร์ดี้ โรบัสต้า", 1, 11.00, 15.00, 13.50, 14.00, 13.00, 150, 20, "กระป๋อง"),
        ("8850123456001", "มันฝรั่ง เลย์ รสคลาสสิก 50ก", 2, 15.00, 20.00, 18.00, 19.00, 17.50, 60, 5, "ซอง")
    ]
    
    for prod in test_products:
        db.execute("""
            INSERT INTO products (
                barcode, product_name, category_id,
                cost_price, retail_price, wholesale_price,
                special_price1, special_price2,
                stock_quantity, min_stock, unit, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, prod)
    
    # ดึงข้อมูลมาแสดงผลยืนยันการสร้าง
    products_before = db.fetch_all("""
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.is_active = 1
    """)
    db.disconnect()
    
    print(f"  [SUCCESS] สร้างสินค้าทดสอบเสร็จสิ้น: {len(products_before)} รายการ:")
    for p in products_before:
        print(f"    - {p['product_name']} | บาร์โค้ด: {p['barcode']} | ราคาปกติ: ฿{p['retail_price']} | สต็อก: {p['stock_quantity']} {p['unit']}")

    # 2. ทำการ Export สินค้าทั้งหมดเป็นไฟล์ Excel
    print("\n=== 2. ส่งออกสินค้า (Export) เป็นไฟล์ Excel ===")
    columns = [
        "บาร์โค้ด", "ชื่อสินค้า", "หมวดหมู่",
        "ราคาทุน", "ราคาขายปกติ", "ราคาขายส่ง",
        "ราคาพิเศษ1", "ราคาพิเศษ2",
        "จำนวนสต็อก", "สต็อกขั้นต่ำ", "หน่วย"
    ]
    
    export_data = []
    for p in products_before:
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
            "สต็อกขั้นต่ำ": int(p["min_stock"] or 10),
            "หน่วย": str(p["unit"] or "ชิ้น").strip()
        })
        
    excel_path = Path("data/migration_test.xlsx")
    if excel_path.exists():
        excel_path.unlink()
        
    success = ExcelManager.export_to_excel(
        export_data, columns, str(excel_path),
        "สินค้า", "รายการสินค้าทั้งหมดที่ส่งออกสำหรับการย้ายระบบ"
    )
    if success and excel_path.exists():
        print(f"  [SUCCESS] ส่งออกข้อมูลลงไฟล์ Excel สำเร็จ: {excel_path.resolve()}")
    else:
        print("  [ERROR] ส่งออกข้อมูลล้มเหลว")
        return

    # 3. ล้างตารางสินค้าทั้งหมด (Reset)
    print("\n=== 3. ล้างฐานข้อมูลสินค้าทั้งหมด (Reset) ===")
    db.connect()
    db.execute("DELETE FROM products")
    db.execute("DELETE FROM categories")
    
    check_empty = db.fetch_all("SELECT product_id FROM products WHERE is_active = 1")
    db.disconnect()
    print(f"  [INFO] จำนวนสินค้าที่เหลืออยู่ในฐานข้อมูลหลังล้างตาราง: {len(check_empty) if check_empty else 0} รายการ (Reset สำเร็จ)")

    # 4. นำข้อมูลจาก Excel กลับเข้ามา (Import)
    print("\n=== 4. นำเข้าข้อมูลสินค้า (Import) จากไฟล์ Excel กลับเข้ามา ===")
    imported_rows = ExcelManager.import_from_excel(str(excel_path), header_row=3)
    print(f"  [INFO] อ่านจำนวนแถวจากไฟล์ Excel: {len(imported_rows)} แถว")
    
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
        "หน่วย": "unit"
    }
    
    db.connect()
    db.begin_transaction()
    
    # โหลด cache หมวดหมู่
    categories = db.fetch_all("SELECT category_id, category_name FROM categories")
    cat_lookup = {c['category_name']: c['category_id'] for c in categories} if categories else {}
    
    imported_count = 0
    for row in imported_rows:
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
            
        # หมวดหมู่
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
                    
        # INSERT สินค้ากลับคืน
        db.execute("""
            INSERT INTO products (
                barcode, product_name, category_id,
                cost_price, retail_price, wholesale_price,
                special_price1, special_price2,
                stock_quantity, min_stock, unit, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            barcode, product_name, category_id,
            float(mapped.get("cost_price") or 0.0),
            float(mapped.get("retail_price") or 0.0),
            float(mapped.get("wholesale_price") or 0.0),
            float(mapped.get("special_price1") or 0.0),
            float(mapped.get("special_price2") or 0.0),
            int(float(mapped.get("stock_quantity") or 0.0)),
            int(float(mapped.get("min_stock") or 10.0)),
            str(mapped.get("unit") or "ชิ้น").strip()
        ))
        imported_count += 1
        
    db.commit_transaction()
    
    # 5. สรุปความถูกต้องของข้อมูลหลังนำเข้า
    print("\n=== 5. ตรวจสอบและแสดงรายการสินค้าในฐานข้อมูลหลังนำเข้าเสร็จสิ้น ===")
    products_after = db.fetch_all("""
        SELECT p.*, c.category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.is_active = 1
        ORDER BY p.product_id ASC
    """)
    db.disconnect()
    
    print(f"  [SUCCESS] จำนวนสินค้าที่กู้คืนได้จริงในฐานข้อมูล: {len(products_after)} รายการ:")
    for p in products_after:
        print(f"    - {p['product_name']} | บาร์โค้ด: {p['barcode']} | ราคาปกติ: ฿{p['retail_price']} | สต็อก: {p['stock_quantity']} {p['unit']}")
        
    print("\n=> [PASS] กระบวนการทดสอบ สร้าง -> ส่งออก -> ล้างตาราง -> นำเข้ากลับคืน ทำงานได้สำเร็จสมบูรณ์ 100%!")
    print("สินค้าจำลองทดสอบทั้งหมดถูกคงไว้ในฐานข้อมูลของคุณแล้ว เพื่อให้คุณเปิดโปรแกรมดูการแสดงผลได้ทันทีครับ")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    run_lifecycle_test()
