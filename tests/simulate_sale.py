# -*- coding: utf-8 -*-
"""
End-to-End POS Sale Simulation
จำลองการทำรายการขายจริงลงในฐานข้อมูล และสั่งพิมพ์ใบเสร็จผ่าน XP-58 (copy 1)
"""
import sys
from pathlib import Path
from datetime import datetime

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import DatabaseManager
from utils.printer_utils import PrinterManager

def run_pos_simulation():
    db = DatabaseManager()
    if not db.connect():
        print("[ERROR] ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
        return
        
    print("=== เริ่มการจำลองการขายแบบ End-to-End ===")
    
    try:
        # 1. ค้นหาสินค้าตัวอย่างในระบบ หากไม่มีให้สร้างใหม่เพื่อทดสอบ
        print("1. ตรวจสอบสินค้าในคลัง...")
        product = db.fetch_one("SELECT * FROM products WHERE is_active = 1 LIMIT 1")
        if not product:
            # สร้างสินค้าจำลอง
            db.execute("""
                INSERT INTO products (barcode, product_name, cost_price, retail_price, stock_quantity, min_stock)
                VALUES ('885012345678', 'กาแฟปรุงสำเร็จ ตรานกแก้ว', 15.00, 25.00, 100, 5)
            """)
            product = db.fetch_one("SELECT * FROM products WHERE barcode = '885012345678'")
            print("  [INFO] สร้างสินค้าทดลองแล้ว: กาแฟปรุงสำเร็จ ตรานกแก้ว")
            
        print(f"  สินค้าที่จะขาย: {product['product_name']} | ราคา: {product['retail_price']} บาท | สต็อกก่อนขาย: {product['stock_quantity']} ชิ้น")
        
        # 2. สร้างเลขที่ใบเสร็จ
        sale_number = db.generate_sale_number()
        sale_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"2. สร้างรหัสใบเสร็จใหม่: {sale_number}")
        
        # 3. เริ่มกระบวนการทำรายการขาย (DB Transaction)
        db.begin_transaction()
        
        # คำนวณยอดเงิน
        qty_to_sell = 2
        unit_price = product['retail_price']
        total_price = qty_to_sell * unit_price
        
        # เพิ่มข้อมูลในตาราง sales
        db.execute("""
            INSERT INTO sales (sale_number, sale_date, user_id, customer_name, subtotal, total_amount, paid_amount, change_amount, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sale_number, sale_date, 1, 'ลูกค้าทั่วไป', total_price, total_price, total_price + 100.0, 100.0, 'cash'))
        
        # ดึง sale_id ที่เพิ่งสร้าง
        sale_row = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (sale_number,))
        sale_id = sale_row['sale_id']
        
        # เพิ่มรายละเอียดใน sale_items
        db.execute("""
            INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sale_id, product['product_id'], product['product_name'], qty_to_sell, unit_price, total_price))
        
        # ตัดสต็อกสินค้า
        db.execute("""
            UPDATE products 
            SET stock_quantity = stock_quantity - ? 
            WHERE product_id = ?
        """, (qty_to_sell, product['product_id']))
        
        db.commit_transaction()
        print("3. บันทึกประวัติการขายและหักลบจำนวนสินค้าในสต็อกสำเร็จ!")
        
        # ดึงสินค้าล่าสุดมาเช็คสต็อกหลังขาย
        product_updated = db.fetch_one("SELECT stock_quantity FROM products WHERE product_id = ?", (product['product_id'],))
        print(f"  สต็อกหลังขาย: {product_updated['stock_quantity']} ชิ้น")
        
        # 4. ดึงข้อมูลประวัติการขายที่บันทึกมาแปลงรูปสำหรับส่งเข้าเครื่องพิมพ์
        print("4. ส่งพิมพ์ใบเสร็จผ่านเครื่องพิมพ์ XP-58 (copy 1)...")
        
        # ดึงรายละเอียดสินค้าที่ซื้อ
        items = db.fetch_all("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,))
        
        receipt_data = {
            'sale_number': sale_number,
            'sale_date': sale_date,
            'company': {
                'name': 'ร้านสะดวกซื้อ PSoft',
                'address': '999 ถนนรัชดาภิเษก เขตจตุจักร กรุงเทพ',
                'phone': '02-999-8888',
                'tax_id': '1234567890123'
            },
            'items': [dict(item) for item in items],
            'total_amount': total_price,
            'paid_amount': total_price + 100.0,
            'change_amount': 100.0,
            'cashier': 'แอดมินระบบ'
        }
        
        pm = PrinterManager()
        pm.printer_name = "XP-58 (copy 1)"
        pm.printer_type = "windows"
        pm.paper_size = "58mm"
        
        success = pm.print_receipt(receipt_data)
        print("  ผลลัพธ์การสั่งพิมพ์:", "สำเร็จ" if success else "ล้มเหลว")
        
    except Exception as e:
        db.rollback_transaction()
        print(f"  [ERROR] การทดลองขายล้มเหลว: {e}")
    finally:
        db.disconnect()
        
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    run_pos_simulation()
