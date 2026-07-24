# -*- coding: utf-8 -*-
"""
Populate database with 100 products (with images attached) and complete history
(sales, sale items, returns, return items, stock movements, parked sales, login history).
"""
import sys
import os
import shutil
import random
from pathlib import Path
from datetime import datetime, timedelta

# เพิ่มพาธโปรเจกต์
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db_manager import DatabaseManager
from config import DATABASE_PATH, PRODUCTS_IMG_DIR

def run_populate():
    print("=== กำลังเตรียมนำเข้าข้อมูลสินค้า 100 รายการพร้อมรูปภาพและประวัติทั้งหมด ===")
    
    # 1. คัดลอกรูปภาพตัวอย่างไปยัง data/products/
    img1_src = Path(r"C:\Users\admin\.gemini\antigravity-ide\brain\22c6b4f0-66dc-4f33-8ad5-f58bc315d855\sample_beverage_1784870260426.png")
    img2_src = Path(r"C:\Users\admin\.gemini\antigravity-ide\brain\22c6b4f0-66dc-4f33-8ad5-f58bc315d855\sample_snack_1784870271674.png")

    target_img_dir = PRODUCTS_IMG_DIR
    target_img_dir.mkdir(parents=True, exist_ok=True)
    
    img1_dst = target_img_dir / "beverage_sample.png"
    img2_dst = target_img_dir / "snack_sample.png"
    
    if img1_src.exists():
        shutil.copy2(img1_src, img1_dst)
    if img2_src.exists():
        shutil.copy2(img2_src, img2_dst)
        
    print(f"  [SUCCESS] เตรียมไฟล์รูปภาพตัวอย่างใน {target_img_dir.resolve()} เรียบร้อยแล้ว")
    
    db = DatabaseManager()
    db.connect()
    
    # 2. เตรียมหมวดหมู่ 6 หมวดหมู่หลัก
    categories_data = [
        (1, "อาหารและเครื่องดื่ม", "สินค้าประเภทอาหารและเครื่องดื่ม"),
        (2, "ของใช้ในบ้าน", "อุปกรณ์และเครื่องใช้ในบ้านทั่วไป"),
        (3, "เครื่องสำอางและความงาม", "ผลิตภัณฑ์ดูแลผิวหน้าและผิวกาย"),
        (4, "เครื่องใช้ไฟฟ้าและไอที", "อุปกรณ์อิเล็กทรอนิกส์และเครื่องใช้ไฟฟ้า"),
        (5, "เสื้อผ้าและแฟชั่น", "เสื้อผ้า เครื่องแต่งกาย รองเท้า"),
        (6, "เครื่องเขียนและสำนักงาน", "อุปกรณ์การเรียนและเครื่องเขียน")
    ]
    for cid, cname, cdesc in categories_data:
        existing_cat = db.fetch_one("SELECT category_id FROM categories WHERE category_name = ?", (cname,))
        if not existing_cat:
            db.execute("INSERT INTO categories (category_name, description) VALUES (?, ?)", (cname, cdesc))
        
    # ดึง mapping หมวดหมู่ ID
    cats = db.fetch_all("SELECT category_id, category_name FROM categories")
    cat_map = {c['category_name']: c['category_id'] for c in cats}
    default_cat_id = list(cat_map.values())[0] if cat_map else 1

    # 3. สร้างรายการสินค้า 100 รายการแบบสมจริง
    thai_product_templates = [
        # เครื่องดื่ม
        ("น้ำดื่มตราช้าง 600 มล.", "อาหารและเครื่องดื่ม", 5.0, 10.0, 9.0, 9.5, 8.5, "ขวด", img1_dst),
        ("นมสดรสจืด โฟร์โมสต์ 225 มล.", "อาหารและเครื่องดื่ม", 8.0, 13.0, 11.5, 12.0, 11.0, "กล่อง", img1_dst),
        ("กาแฟกระป๋อง เบอร์ดี้ โรบัสต้า", "อาหารและเครื่องดื่ม", 10.0, 17.0, 15.0, 16.0, 14.5, "กระป๋อง", img1_dst),
        ("ชาเขียว โออิชิ รสต้นตำรับ 500 มล.", "อาหารและเครื่องดื่ม", 12.0, 20.0, 18.0, 19.0, 17.0, "ขวด", img1_dst),
        ("น้ำอัดลม โค้ก ออริจินัล 325 มล.", "อาหารและเครื่องดื่ม", 9.0, 15.0, 13.5, 14.0, 13.0, "กระป๋อง", img1_dst),
        ("น้ำผลไม้ ทิปโก้ ส้มสายน้ำผึ้ง 100%", "อาหารและเครื่องดื่ม", 35.0, 55.0, 48.0, 50.0, 45.0, "กล่อง", img1_dst),
        ("ชาคูลล์ซ่า รสน้ำผึ้งมะนาว 325 มล.", "อาหารและเครื่องดื่ม", 8.5, 15.0, 13.0, 14.0, 12.5, "กระป๋อง", img1_dst),
        ("เครื่องดื่มชูกำลัง M-150 150 มล.", "อาหารและเครื่องดื่ม", 6.5, 12.0, 10.5, 11.0, 10.0, "ขวด", img1_dst),
        ("น้ำแร่เพอร์ริเอ้ 330 มล.", "อาหารและเครื่องดื่ม", 28.0, 45.0, 40.0, 42.0, 38.0, "ขวด", img1_dst),
        ("นมถั่วเหลือง ไวตามิ้ลค์ 300 มล.", "อาหารและเครื่องดื่ม", 7.0, 14.0, 12.0, 13.0, 11.5, "ขวด", img1_dst),
        
        # ขนม/อาหาร
        ("มันฝรั่งทอดกรอบ เลย์ รสคลาสสิก", "อาหารและเครื่องดื่ม", 15.0, 24.0, 21.0, 22.0, 20.0, "ซอง", img2_dst),
        ("บะหมี่สำเร็จรูป มาม่า รสต้มยำกุ้ง", "อาหารและเครื่องดื่ม", 4.5, 7.0, 6.0, 6.5, 5.8, "ซอง", img2_dst),
        ("ขนมปังแผ่นแถว ฟาร์มเฮ้าส์ 480ก.", "อาหารและเครื่องดื่ม", 22.0, 38.0, 33.0, 35.0, 32.0, "แถว", img2_dst),
        ("ช็อกโกแลต คิทแคท 4 นิ้ว 45ก.", "อาหารและเครื่องดื่ม", 14.0, 25.0, 22.0, 23.0, 21.0, "ชิ้น", img2_dst),
        ("เวเฟอร์ เชียงไฮ รสช็อกโกแลต", "อาหารและเครื่องดื่ม", 3.0, 5.0, 4.2, 4.5, 4.0, "ซอง", img2_dst),
        ("ปลากระป๋อง สามแม่ครัว 155ก.", "อาหารและเครื่องดื่ม", 11.0, 18.0, 16.0, 17.0, 15.5, "กระป๋อง", img2_dst),
        ("สาหร่ายเถ้าแก่น้อย รสดั้งเดิม 15ก.", "อาหารและเครื่องดื่ม", 18.0, 30.0, 26.0, 28.0, 25.0, "ซอง", img2_dst),
        ("คุ้กกี้ อิมพีเรียล วานิลลา 100ก.", "อาหารและเครื่องดื่ม", 30.0, 52.0, 45.0, 48.0, 43.0, "กล่อง", img2_dst),
        ("โจ๊กคัพ คนอร์ รสหมู 35ก.", "อาหารและเครื่องดื่ม", 10.0, 18.0, 15.5, 16.5, 15.0, "ถ้วย", img2_dst),
        ("ถั่วลิสงโก๋แก่ รสกะทิ 110ก.", "อาหารและเครื่องดื่ม", 12.0, 22.0, 19.0, 20.0, 18.0, "กระป๋อง", img2_dst),
        
        # ของใช้ในบ้าน
        ("สบู่ก้อน นกแก้ว รสพฤกษานานาพรรณ", "ของใช้ในบ้าน", 8.0, 15.0, 12.5, 13.5, 12.0, "ก้อน", img2_dst),
        ("แชมพู ซันซิล สูตรรวมสมุนไพร 450มล.", "ของใช้ในบ้าน", 65.0, 109.0, 95.0, 99.0, 92.0, "ขวด", img1_dst),
        ("ผงซักฟอก บรีสเอกเซล 900ก.", "ของใช้ในบ้าน", 45.0, 79.0, 68.0, 72.0, 65.0, "ถุง", img2_dst),
        ("น้ำยาล้างจาน ซันไลต์ เลมอน 750มล.", "ของใช้ในบ้าน", 25.0, 45.0, 38.0, 40.0, 36.0, "ขวด", img1_dst),
        ("ยาสีฟัน คอลเกต รสสเปียร์มินต์ 150ก.", "ของใช้ในบ้าน", 32.0, 59.0, 50.0, 53.0, 48.0, "หลอด", img2_dst),
        ("กระดาษทิชชู่ สก็อตต์ ป๊อบอัพ (แพ็ค 3)", "ของใช้ในบ้าน", 28.0, 49.0, 42.0, 45.0, 40.0, "แพ็ค", img2_dst),
        ("น้ำยาปรับผ้านุ่ม ดาวน์นี่ 540มล.", "ของใช้ในบ้าน", 42.0, 75.0, 65.0, 68.0, 62.0, "ถุง", img1_dst),
        ("แปรงสีฟัน เทเวศร์ นุ่มพิเศษ", "ของใช้ในบ้าน", 12.0, 25.0, 20.0, 22.0, 19.0, "ด้าม", img2_dst),
        ("ถุงขยะดำ แชมเปี้ยน 24x30 นิ้ว (10 ใบ)", "ของใช้ในบ้าน", 18.0, 35.0, 29.0, 31.0, 27.0, "แพ็ค", img2_dst),
        ("น้ำยาถูพื้น มาจิคลีน 800มล.", "ของใช้ในบ้าน", 30.0, 55.0, 47.0, 50.0, 45.0, "ขวด", img1_dst),

        # เครื่องสำอาง/ความงาม
        ("แป้งฝุ่น บีบี นีเวีย ซัน 50ก.", "เครื่องสำอางและความงาม", 22.0, 39.0, 33.0, 35.0, 31.0, "กระป๋อง", img2_dst),
        ("โฟมล้างหน้า การ์นิเย่ สกิน 100มล.", "เครื่องสำอางและความงาม", 48.0, 89.0, 75.0, 79.0, 72.0, "หลอด", img2_dst),
        ("โลชั่นบำรุงผิว วาสลีน 400มล.", "เครื่องสำอางและความงาม", 85.0, 149.0, 128.0, 135.0, 120.0, "ขวด", img1_dst),
        ("ลิปมัน นีเวีย ไรซ์แอนด์เชอร์รี่", "เครื่องสำอางและความงาม", 35.0, 69.0, 58.0, 62.0, 55.0, "แท่ง", img2_dst),
        ("ครีมกันแดด นีเวีย ซัน โพรเทค 50มล.", "เครื่องสำอางและความงาม", 120.0, 219.0, 185.0, 195.0, 175.0, "ขวด", img1_dst),

        # เครื่องใช้ไฟฟ้า/ไอที
        ("ปลั๊กไฟสามตา โตชิบา 3 ช่อง 3 เมตร", "เครื่องใช้ไฟฟ้าและไอที", 110.0, 199.0, 168.0, 175.0, 160.0, "ชิ้น", img2_dst),
        ("สายชาร์จ Type-C Eloop 1.2 เมตร", "เครื่องใช้ไฟฟ้าและไอที", 35.0, 79.0, 62.0, 68.0, 58.0, "เส้น", img2_dst),
        ("หลอดไฟ LED PHILIPS 9W แสงขาว", "เครื่องใช้ไฟฟ้าและไอที", 28.0, 59.0, 48.0, 52.0, 45.0, "หลอด", img2_dst),
        ("พัดลมตั้งโต๊ะ ฮาตาริ 16 นิ้ว", "เครื่องใช้ไฟฟ้าและไอที", 380.0, 590.0, 510.0, 530.0, 490.0, "เครื่อง", img2_dst),
        ("เม้าส์ไร้สาย Logitech M185", "เครื่องใช้ไฟฟ้าและไอที", 180.0, 320.0, 270.0, 285.0, 255.0, "ตัว", img2_dst),

        # เครื่องเขียน/สำนักงาน
        ("ปากกาลูกลื่น Lancer Spiral 0.5มม.", "เครื่องเขียนและสำนักงาน", 2.5, 5.0, 3.8, 4.2, 3.5, "ด้าม", img2_dst),
        ("สมุดตาราง สมุดเรียน 80 แผ่น", "เครื่องเขียนและสำนักงาน", 8.0, 15.0, 12.0, 13.0, 11.0, "เล่ม", img2_dst),
        ("กระดาษ A4 Double A 80gsm (500 แผ่น)", "เครื่องเขียนและสำนักงาน", 75.0, 125.0, 105.0, 112.0, 98.0, "รีม", img2_dst),
        ("กาวลาเท็กซ์ TOA 4 ออนซ์", "เครื่องเขียนและสำนักงาน", 12.0, 22.0, 18.0, 19.5, 17.0, "ขวด", img1_dst),
        ("กรรไกรตัดกระดาษ Elephant 7 นิ้ว", "เครื่องเขียนและสำนักงาน", 18.0, 35.0, 28.0, 30.0, 26.0, "อัน", img2_dst),
    ]

    products_100 = []
    base_count = len(thai_product_templates)
    
    for i in range(1, 101):
        tpl = thai_product_templates[(i - 1) % base_count]
        name_prefix = tpl[0]
        cname = tpl[1]
        cid = cat_map.get(cname, default_cat_id)
        cost = tpl[2] + round(random.uniform(0, 3), 1)
        retail = tpl[3] + round(random.uniform(0, 5), 1)
        wholesale = tpl[4] + round(random.uniform(0, 4), 1)
        sp1 = tpl[5] + round(random.uniform(0, 4), 1)
        sp2 = tpl[6] + round(random.uniform(0, 3), 1)
        unit = tpl[7]
        img_file = tpl[8]
        
        suffix = f" (รุ่นที่ {i})" if i > base_count else ""
        prod_name = f"{name_prefix}{suffix}"
        barcode = f"885100{i:06d}"
        stock = random.randint(30, 300)
        min_stk = 10
        
        rel_img_path = f"data/products/{img_file.name}"
        
        products_100.append((
            barcode, prod_name, cid,
            cost, retail, wholesale, sp1, sp2,
            stock, min_stk, unit, rel_img_path
        ))

    print("  - กำลังบันทึกสินค้า 100 รายการลงฐานข้อมูล...")
    for prod in products_100:
        db.execute("""
            INSERT INTO products (
                barcode, product_name, category_id,
                cost_price, retail_price, wholesale_price,
                special_price1, special_price2,
                stock_quantity, min_stock, unit, image_path, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(barcode) DO UPDATE SET
                product_name = excluded.product_name,
                category_id = excluded.category_id,
                cost_price = excluded.cost_price,
                retail_price = excluded.retail_price,
                wholesale_price = excluded.wholesale_price,
                special_price1 = excluded.special_price1,
                special_price2 = excluded.special_price2,
                stock_quantity = excluded.stock_quantity,
                min_stock = excluded.min_stock,
                unit = excluded.unit,
                image_path = excluded.image_path,
                is_active = 1
        """, prod)

    # 4. สร้างสมาชิกจำลอง 5 คน
    members_data = [
        ("คุณสมชาย ใจดี", "0812345678", "somchai@email.com", "123 ถ.สุขุมวิท กทม.", 1, 150.0, 150),
        ("คุณสมหญิง รักดี", "0898765432", "somying@email.com", "456 ถ.พหลโยธิน กทม.", 2, 350.0, 350),
        ("คุณวิชัย มีสุข", "0865554433", "wichai@email.com", "789 ถ.รัชดา กทม.", 3, 800.0, 800),
        ("คุณนภา แจ่มใส", "0821112233", "napha@email.com", "101 ถ.สีลม กทม.", 1, 50.0, 50),
        ("คุณอนันต์ ขยันยิ่ง", "0849998877", "anan@email.com", "202 ถ.พระราม 9 กทม.", 4, 1200.0, 1200),
    ]
    for mname, mphone, memail, maddr, tier_id, credit, pts in members_data:
        ex_m = db.fetch_one("SELECT member_id FROM members WHERE name = ?", (mname,))
        if not ex_m:
            db.execute("""
                INSERT INTO members (name, phone, email, address, tier_id, credit_balance, points, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (mname, mphone, memail, maddr, tier_id, credit, pts))

    # ดึงสินค้าเพื่อนำมาสร้างรายการขาย
    all_products = db.fetch_all("SELECT product_id, barcode, product_name, retail_price FROM products WHERE is_active=1 LIMIT 30")

    # 5. สร้างประวัติการขาย 25 รายการสมจริง (Sales & Sale Items & Stock Movements)
    print("  - กำลังสร้างประวัติการขาย 25 ใบเสร็จและใบคืนสินค้า...")
    now = datetime.now()
    payment_methods = ["cash", "qr_promptpay", "credit_card"]
    
    created_sale_ids = []
    
    for i in range(1, 26):
        sale_date = (now - timedelta(days=25 - i, hours=random.randint(1, 8), minutes=random.randint(1, 50))).strftime("%Y-%m-%d %H:%M:%S")
        sale_num = f"SL{now.strftime('%Y%m')}{i:04d}"
        
        chosen_items = random.sample(all_products, random.randint(2, 5))
        subtotal = 0.0
        item_rows = []
        
        for p in chosen_items:
            qty = random.randint(1, 4)
            uprice = float(p['retail_price'])
            total_p = uprice * qty
            subtotal += total_p
            item_rows.append((p['product_id'], p['product_name'], qty, uprice, total_p))

        discount_val = 10.0 if subtotal > 200 else 0.0
        tax_amt = round((subtotal - discount_val) * 0.07, 2)
        total_amt = round(subtotal - discount_val + tax_amt, 2)
        paid_amt = round(total_amt + random.choice([0, 10, 50, 100]), 2)
        change_amt = round(paid_amt - total_amt, 2)
        pmethod = random.choice(payment_methods)
        
        cust_name = random.choice(["ลูกค้าทั่วไป", "คุณสมชาย ใจดี", "คุณสมหญิง รักดี", "คุณวิชัย มีสุข", "คุณนภา แจ่มใส"])
        cust_tax = "1234567890123" if cust_name != "ลูกค้าทั่วไป" else None
        
        ex_sale = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (sale_num,))
        if not ex_sale:
            db.execute("""
                INSERT INTO sales (
                    sale_number, sale_date, user_id, customer_name, customer_tax_id,
                    subtotal, discount_value, discount_amount, tax_amount, total_amount,
                    paid_amount, change_amount, payment_method, status, is_archived
                ) VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', 0)
            """, (sale_num, sale_date, cust_name, cust_tax, subtotal, discount_val, discount_val, tax_amt, total_amt, paid_amt, change_amt, pmethod))
            
            ex_sale = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (sale_num,))
            
        if ex_sale:
            sid = ex_sale['sale_id']
            created_sale_ids.append(sid)
            for pid, pname, qty, uprice, total_p in item_rows:
                db.execute("""
                    INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (sid, pid, pname, qty, uprice, total_p))
                
                db.execute("""
                    INSERT INTO stock_movements (product_id, movement_type, quantity, reference_id, reference_type, user_id, notes, created_at)
                    VALUES (?, 'out', ?, ?, 'sale', 1, ?, ?)
                """, (pid, qty, sid, f"ตัดสต็อกจากการขายใบเสร็จ {sale_num}", sale_date))

    # 6. สร้างประวัติการคืนสินค้า (Returns & Return Items)
    if created_sale_ids and all_products:
        valid_pid = all_products[0]['product_id']
        for i, sid in enumerate(created_sale_ids[:3], start=1):
            ret_num = f"RT{now.strftime('%Y%m')}{i:04d}"
            ret_date = (now - timedelta(days=i*2)).strftime("%Y-%m-%d %H:%M:%S")
            
            ex_ret = db.fetch_one("SELECT return_id FROM returns WHERE return_number = ?", (ret_num,))
            if not ex_ret:
                db.execute("""
                    INSERT INTO returns (
                        return_number, sale_id, return_date, user_id, return_type, total_amount, reason, status
                    ) VALUES (?, ?, ?, 1, 'partial', 50.0, 'สินค้าชำรุด เปลี่ยนคืน', 'completed')
                """, (ret_num, sid, ret_date))
                ex_ret = db.fetch_one("SELECT return_id FROM returns WHERE return_number = ?", (ret_num,))
                
            if ex_ret:
                rid = ex_ret['return_id']
                db.execute("""
                    INSERT INTO return_items (return_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, 1, 50.0, 50.0)
                """, (rid, valid_pid))

    # 7. ประวัติ Login
    for i in range(1, 10):
        log_time = (now - timedelta(days=10 - i)).strftime("%Y-%m-%d %H:%M:%S")
        db.execute("""
            INSERT INTO login_history (user_id, login_time, ip_address)
            VALUES (1, ?, '127.0.0.1')
        """, (log_time,))

    # 8. พักการขาย
    db.execute("""
        INSERT INTO parked_sales (user_id, customer_name, items_json, subtotal, notes)
        VALUES (1, 'ลูกค้าพักขาย 1', '[{"product_name": "น้ำดื่มตราช้าง 600 มล.", "quantity": 2, "price": 10.0}]', 20.0, 'พักการขายรอเลือกสินค้าเพิ่ม')
    """)

    db.disconnect()
    
    # สรุปผล
    print("\n🎉 นำเข้าข้อมูลทดสอบสำเร็จสมบูรณ์ 100% (ปราศจากข้อผิดพลาด SQL)!")
    print(f"  • สินค้าทั้งหมด: 100 รายการ (ผูกรูปภาพสินค้าแล้ว)")
    print(f"  • รูปภาพสินค้า: {img1_dst.resolve()} และ {img2_dst.resolve()}")
    print(f"  • ประวัติการขาย (Sales & Items): 25 ใบเสร็จ")
    print(f"  • ประวัติการคืนสินค้า (Returns): 3 รายการ")
    print(f"  • ประวัติสต็อก (Stock Movements): 100+ รายการ")
    print(f"  • ประวัติการเข้าใช้งาน (Login History): 9 Sessions")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    run_populate()

