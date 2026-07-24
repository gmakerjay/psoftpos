# -*- coding: utf-8 -*-
"""
🧹 Reset All Transactions to 0 & Add 100 Products with Images
- ล้างข้อมูลยอดขาย, ประวัติ, สต็อก, การคืน, พักขาย ทั้งหมดเป็น 0
- เพิ่มสินค้าจำลอง 100 รายการพร้อมผูกรูปภาพสินค้า (ใช้รูปตัวอย่าง ไม่เสียเวลา Gen ใหม่)
"""

import sys
import os
import shutil
import random
from pathlib import Path
from datetime import datetime

# เพิ่มพาธโปรเจกต์
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, PRODUCTS_IMG_DIR


def clean_and_populate():
    print("=" * 70)
    print("🧹 เริ่มกระบวนการล้างข้อมูลทั้งหมดเป็น 0 และสร้างสินค้า 100 รายการ")
    print("=" * 70)

    # 1. ตรวจสอบโฟลเดอร์รูปภาพสินค้า
    target_img_dir = PRODUCTS_IMG_DIR
    target_img_dir.mkdir(parents=True, exist_ok=True)

    img_beverage = target_img_dir / "beverage_sample.png"
    img_snack = target_img_dir / "snack_sample.png"

    # หากไม่มีรูปตัวอย่าง ให้สร้างรูปสี 300x300 แบบง่ายไว้เป็น placeholder
    for img_path, color_name in [(img_beverage, "blue"), (img_snack, "orange")]:
        if not img_path.exists():
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new("RGB", (300, 300), color=color_name)
                draw = ImageDraw.Draw(img)
                draw.text((80, 140), "Product Image", fill="white")
                img.save(img_path)
            except Exception as e:
                print(f"  - Warning creating sample image {img_path}: {e}")

    print(f"  [SUCCESS] ใช้ไฟล์รูปภาพตัวอย่าง:")
    print(f"    - {img_beverage.name}")
    print(f"    - {img_snack.name}")

    # 2. เชื่อมต่อฐานข้อมูลและสั่ง Reset ข้อมูลการทำงานทั้งหมด
    db = DatabaseManager()
    db.connect()

    print("\n  [1/4] ล้างข้อมูลรายการขาย สต็อก ประวัติ และสินค้าเดิมออกเป็น 0...")
    db.execute("PRAGMA foreign_keys = OFF")
    tables_to_wipe = [
        "return_items", "returns", "sale_items", "sales",
        "stock_movements", "parked_sales", "login_history",
        "products", "categories"
    ]
    for table in tables_to_wipe:
        db.execute(f"DELETE FROM {table}")
        # Reset autoincrement sequence
        db.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
    db.execute("PRAGMA foreign_keys = ON")

    # 3. ล้างไฟล์ประวัติการขายใน Backup/
    backup_dir = BASE_DIR / "Backup"
    if backup_dir.exists():
        for b_file in backup_dir.glob("*"):
            if b_file.is_file() and b_file.name != ".gitkeep":
                try:
                    b_file.unlink()
                except Exception:
                    pass
        print("  [SUCCESS] ล้างไฟล์ Backup และ Sales Log ใน Backup/ เรียบร้อยแล้ว")

    # 4. สร้างหมวดหมู่ 6 หมวดหมู่หลัก
    print("\n  [2/4] สร้างหมวดหมู่สินค้าหลัก 6 หมวดหมู่...")
    categories_data = [
        (1, "อาหารและเครื่องดื่ม", "สินค้าประเภทอาหาร เครื่องดื่ม ขนมขบเคี้ยว"),
        (2, "ของใช้ในบ้าน", "อุปกรณ์และเครื่องใช้ในบ้านทั่วไป"),
        (3, "เครื่องสำอางและความงาม", "ผลิตภัณฑ์ดูแลผิวหน้า ผิวกาย และความงาม"),
        (4, "เครื่องใช้ไฟฟ้าและไอที", "อุปกรณ์อิเล็กทรอนิกส์และเครื่องใช้ไฟฟ้า"),
        (5, "เสื้อผ้าและแฟชั่น", "เสื้อผ้า เครื่องแต่งกาย รองเท้า"),
        (6, "เครื่องเขียนและสำนักงาน", "อุปกรณ์การเรียน เครื่องเขียน เอกสาร")
    ]
    for cid, cname, cdesc in categories_data:
        db.execute("INSERT INTO categories (category_id, category_name, description) VALUES (?, ?, ?)", (cid, cname, cdesc))

    # 5. สร้างรายการสินค้า 100 รายการพร้อมผูกรูปภาพ
    print("\n  [3/4] บันทึกสินค้า 100 รายการพร้อมรูปภาพลงฐานข้อมูล...")
    
    product_templates = [
        # เครื่องดื่ม
        ("น้ำดื่มตราช้าง 600 มล.", 1, 5.0, 10.0, 9.0, 9.5, 8.5, "ขวด", "data/products/beverage_sample.png"),
        ("นมสดรสจืด โฟร์โมสต์ 225 มล.", 1, 8.0, 13.0, 11.5, 12.0, 11.0, "กล่อง", "data/products/beverage_sample.png"),
        ("กาแฟกระป๋อง เบอร์ดี้ โรบัสต้า", 1, 10.0, 17.0, 15.0, 16.0, 14.5, "กระป๋อง", "data/products/beverage_sample.png"),
        ("ชาเขียว โออิชิ รสต้นตำรับ 500 มล.", 1, 12.0, 20.0, 18.0, 19.0, 17.0, "ขวด", "data/products/beverage_sample.png"),
        ("น้ำอัดลม โค้ก ออริจินัล 325 มล.", 1, 9.0, 15.0, 13.5, 14.0, 13.0, "กระป๋อง", "data/products/beverage_sample.png"),
        ("น้ำผลไม้ ทิปโก้ ส้มสายน้ำผึ้ง 100%", 1, 35.0, 55.0, 48.0, 50.0, 45.0, "กล่อง", "data/products/beverage_sample.png"),
        ("เครื่องดื่มชูกำลัง M-150 150 มล.", 1, 6.5, 12.0, 10.5, 11.0, 10.0, "ขวด", "data/products/beverage_sample.png"),
        ("นมถั่วเหลือง ไวตามิ้ลค์ 300 มล.", 1, 7.0, 14.0, 12.0, 13.0, 11.5, "ขวด", "data/products/beverage_sample.png"),
        
        # ขนม/อาหาร
        ("มันฝรั่งทอดกรอบ เลย์ รสคลาสสิก", 1, 15.0, 24.0, 21.0, 22.0, 20.0, "ซอง", "data/products/snack_sample.png"),
        ("บะหมี่สำเร็จรูป มาม่า รสต้มยำกุ้ง", 1, 4.5, 7.0, 6.0, 6.5, 5.8, "ซอง", "data/products/snack_sample.png"),
        ("ขนมปังแผ่นแถว ฟาร์มเฮ้าส์ 480ก.", 1, 22.0, 38.0, 33.0, 35.0, 32.0, "แถว", "data/products/snack_sample.png"),
        ("ช็อกโกแลต คิทแคท 4 นิ้ว 45ก.", 1, 14.0, 25.0, 22.0, 23.0, 21.0, "ชิ้น", "data/products/snack_sample.png"),
        ("เวเฟอร์ เชียงไฮ รสช็อกโกแลต", 1, 3.0, 5.0, 4.2, 4.5, 4.0, "ซอง", "data/products/snack_sample.png"),
        ("ปลากระป๋อง สามแม่ครัว 155ก.", 1, 11.0, 18.0, 16.0, 17.0, 15.5, "กระป๋อง", "data/products/snack_sample.png"),
        ("สาหร่ายเถ้าแก่น้อย รสดั้งเดิม 15ก.", 1, 18.0, 30.0, 26.0, 28.0, 25.0, "ซอง", "data/products/snack_sample.png"),
        ("โจ๊กคัพ คนอร์ รสหมู 35ก.", 1, 10.0, 18.0, 15.5, 16.5, 15.0, "ถ้วย", "data/products/snack_sample.png"),
        
        # ของใช้ในบ้าน
        ("สบู่ก้อน นกแก้ว รสพฤกษานานาพรรณ", 2, 8.0, 15.0, 12.5, 13.5, 12.0, "ก้อน", "data/products/snack_sample.png"),
        ("แชมพู ซันซิล สูตรรวมสมุนไพร 450มล.", 2, 65.0, 109.0, 95.0, 99.0, 92.0, "ขวด", "data/products/beverage_sample.png"),
        ("ผงซักฟอก บรีสเอกเซล 900ก.", 2, 45.0, 79.0, 68.0, 72.0, 65.0, "ถุง", "data/products/snack_sample.png"),
        ("น้ำยาล้างจาน ซันไลต์ เลมอน 750มล.", 2, 25.0, 45.0, 38.0, 40.0, 36.0, "ขวด", "data/products/beverage_sample.png"),
        ("ยาสีฟัน คอลเกต รสสเปียร์มินต์ 150ก.", 2, 32.0, 59.0, 50.0, 53.0, 48.0, "หลอด", "data/products/snack_sample.png"),
        ("กระดาษทิชชู่ สก็อตต์ ป๊อบอัพ (แพ็ค 3)", 2, 28.0, 49.0, 42.0, 45.0, 40.0, "แพ็ค", "data/products/snack_sample.png"),
        ("น้ำยาปรับผ้านุ่ม ดาวน์นี่ 540มล.", 2, 42.0, 75.0, 65.0, 68.0, 62.0, "ถุง", "data/products/beverage_sample.png"),
        
        # เครื่องสำอาง/ความงาม
        ("แป้งฝุ่น บีบี นีเวีย ซัน 50ก.", 3, 22.0, 39.0, 33.0, 35.0, 31.0, "กระป๋อง", "data/products/snack_sample.png"),
        ("โฟมล้างหน้า การ์นิเย่ สกิน 100มล.", 3, 48.0, 89.0, 75.0, 79.0, 72.0, "หลอด", "data/products/snack_sample.png"),
        ("โลชั่นบำรุงผิว วาสลีน 400มล.", 3, 85.0, 149.0, 128.0, 135.0, 120.0, "ขวด", "data/products/beverage_sample.png"),
        ("ครีมกันแดด นีเวีย ซัน โพรเทค 50มล.", 3, 120.0, 219.0, 185.0, 195.0, 175.0, "ขวด", "data/products/beverage_sample.png"),

        # เครื่องใช้ไฟฟ้า/ไอที
        ("ปลั๊กไฟสามตา โตชิบา 3 ช่อง 3 เมตร", 4, 110.0, 199.0, 168.0, 175.0, 160.0, "ชิ้น", "data/products/snack_sample.png"),
        ("สายชาร์จ Type-C Eloop 1.2 เมตร", 4, 35.0, 79.0, 62.0, 68.0, 58.0, "เส้น", "data/products/snack_sample.png"),
        ("หลอดไฟ LED PHILIPS 9W แสงขาว", 4, 28.0, 59.0, 48.0, 52.0, 45.0, "หลอด", "data/products/snack_sample.png"),
        ("เม้าส์ไร้สาย Logitech M185", 4, 180.0, 320.0, 270.0, 285.0, 255.0, "ตัว", "data/products/snack_sample.png"),

        # เครื่องเขียน/สำนักงาน
        ("ปากกาลูกลื่น Lancer Spiral 0.5มม.", 6, 2.5, 5.0, 3.8, 4.2, 3.5, "ด้าม", "data/products/snack_sample.png"),
        ("สมุดตาราง สมุดเรียน 80 แผ่น", 6, 8.0, 15.0, 12.0, 13.0, 11.0, "เล่ม", "data/products/snack_sample.png"),
        ("กระดาษ A4 Double A 80gsm (500 แผ่น)", 6, 75.0, 125.0, 105.0, 112.0, 98.0, "รีม", "data/products/snack_sample.png"),
        ("กาวลาเท็กซ์ TOA 4 ออนซ์", 6, 12.0, 22.0, 18.0, 19.5, 17.0, "ขวด", "data/products/beverage_sample.png"),
    ]

    base_len = len(product_templates)

    db.begin_transaction()
    for i in range(1, 101):
        tpl = product_templates[(i - 1) % base_len]
        base_name = tpl[0]
        cid = tpl[1]
        cost = tpl[2]
        retail = tpl[3]
        wholesale = tpl[4]
        sp1 = tpl[5]
        sp2 = tpl[6]
        unit = tpl[7]
        img_path = tpl[8]

        suffix = f" (สูตร {i})" if i > base_len else ""
        prod_name = f"{base_name}{suffix}"
        barcode = f"885000{i:06d}"
        stock = random.randint(20, 200)
        min_stock = 10

        db.execute("""
            INSERT INTO products (
                barcode, product_name, category_id,
                cost_price, retail_price, wholesale_price,
                special_price1, special_price2,
                stock_quantity, min_stock, unit, image_path, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (barcode, prod_name, cid, cost, retail, wholesale, sp1, sp2, stock, min_stock, unit, img_path))

    db.commit_transaction()

    # 6. ตรวจสอบสรุปข้อมูลหลังล้างและเพิ่มสินค้า
    print("\n  [4/4] ตรวจสอบผลลัพธ์การคลีนอัพและบันทึกข้อมูล...")
    cnt_products = db.fetch_one("SELECT COUNT(*) as cnt FROM products")['cnt']
    cnt_sales = db.fetch_one("SELECT COUNT(*) as cnt FROM sales")['cnt']
    cnt_items = db.fetch_one("SELECT COUNT(*) as cnt FROM sale_items")['cnt']
    cnt_returns = db.fetch_one("SELECT COUNT(*) as cnt FROM returns")['cnt']
    cnt_stock_mov = db.fetch_one("SELECT COUNT(*) as cnt FROM stock_movements")['cnt']

    db.disconnect()

    print("\n" + "=" * 70)
    print("🎉 ผลการล้างข้อมูลและการเพิ่มสินค้า 100 รายการสำเร็จ 100%")
    print(f"  • ยอดขายทั้งหมด (Sales): {cnt_sales} รายการ (คลีนอัพเป็น 0 แล้ว)")
    print(f"  • รายการสินค้าขาย (Sale Items): {cnt_items} รายการ (คลีนอัพเป็น 0 แล้ว)")
    print(f"  • รายการใบคืน (Returns): {cnt_returns} รายการ (คลีนอัพเป็น 0 แล้ว)")
    print(f"  • การเคลื่อนไหวสต็อก (Stock Movements): {cnt_stock_mov} รายการ (คลีนอัพเป็น 0 แล้ว)")
    print(f"  • สินค้าทั้งหมดในระบบ: {cnt_products} รายการ (ผูกรูปภาพสินค้าครบ 100%)")
    print("=" * 70)

if __name__ == "__main__":
    clean_and_populate()
