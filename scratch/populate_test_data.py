# -*- coding: utf-8 -*-
"""
Populate database with 4 test products permanently
"""
import sys
from pathlib import Path

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager

def populate():
    db = DatabaseManager()
    db.connect()
    
    # ล้างตาราง
    db.execute("DELETE FROM products")
    db.execute("DELETE FROM categories")
    
    # สร้างหมวดหมู่
    db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (1, 'เครื่องดื่ม')")
    db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (2, 'ขนมขบเคี้ยว')")
    
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
        
    db.commit_transaction()
    db.disconnect()
    print("SUCCESS: 4 test products populated permanently.")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    populate()
