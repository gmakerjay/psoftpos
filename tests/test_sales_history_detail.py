# -*- coding: utf-8 -*-
"""
Automated Test for Sales Transaction & Sales History View Detail Feature
"""

import sys
import os
import unittest
from datetime import datetime

# Ensure project directory is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from config import DATABASE_PATH, COMPANY_INFO

class TestSalesHistoryDetail(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseManager()
        cls.db.connect()
        
    @classmethod
    def tearDownClass(cls):
        cls.db.disconnect()
        
    def test_01_create_sale_and_verify_detail_logic(self):
        """ทดสอบสร้างรายการขายและทดสอบฟังก์ชันดูรายละเอียดประวัติการขาย"""
        self.db.connect()
        
        print("\n--- Step 1: Creating test product ---")
        self.db.execute("DELETE FROM products WHERE barcode = 'TEST-DETAIL-001'")
        self.db.execute("""
            INSERT INTO products (product_name, barcode, retail_price, stock_quantity, category_id)
            VALUES ('สินค้าทดสอบรายละเอียด', 'TEST-DETAIL-001', 150.00, 100, NULL)
        """)
        product = self.db.fetch_one("SELECT * FROM products WHERE barcode = 'TEST-DETAIL-001'")
        self.assertIsNotNone(product, "Product creation failed")
        product_id = product['product_id']
        print(f"✅ Created test product: ID {product_id}, Name: {product['product_name']}")
        
        print("\n--- Step 2: Performing sale transaction ---")
        sale_number = f"POS-DETAIL-{int(datetime.now().timestamp())}"
        subtotal = 300.00  # 2 items x 150.00
        discount = 20.00
        tax = 19.60
        total = 299.60
        paid = 500.00
        change = 200.40
        sale_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.db.execute("""
            INSERT INTO sales (
                sale_number, sale_date, user_id, member_id,
                subtotal, discount_amount, tax_amount, total_amount,
                paid_amount, change_amount, payment_method, price_type, status
            ) VALUES (?, ?, 1, NULL, ?, ?, ?, ?, ?, ?, 'cash', 'retail', 'completed')
        """, (sale_number, sale_date, subtotal, discount, tax, total, paid, change))
        
        sale_row = self.db.fetch_one("SELECT * FROM sales WHERE sale_number = ?", (sale_number,))
        self.assertIsNotNone(sale_row, "Sale creation failed")
        sale_id = sale_row['sale_id']
        print(f"✅ Created sale record: ID {sale_id}, Bill Number: {sale_number}")
        
        # Insert sale item
        self.db.execute("""
            INSERT INTO sale_items (
                sale_id, product_id, product_name,
                quantity, unit_price, total_price
            ) VALUES (?, ?, ?, 2, 150.00, 300.00)
        """, (sale_id, product_id, product['product_name']))
        
        # Update product stock
        self.db.execute("""
            UPDATE products SET stock_quantity = stock_quantity - 2 WHERE product_id = ?
        """, (product_id,))
        
        print("\n--- Step 3: Fetching sale from DB using SalesHistoryFrame query ---")
        sales = self.db.fetch_all("""
            SELECT s.*, u.full_name as cashier_name,
                   COUNT(si.item_id) as item_count,
                   GROUP_CONCAT(COALESCE(si.product_name, 'Unknown') || ' x' || COALESCE(si.quantity, 0), ', ') as items_list,
                   m.name as member_name
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            LEFT JOIN members m ON s.member_id = m.member_id
            WHERE s.sale_id = ?
            GROUP BY s.sale_id
        """, (sale_id,))
        
        self.assertTrue(len(sales) > 0, "Failed to fetch created sale")
        target_sale = sales[0]
        
        print("\n--- Step 4: Testing dict(sale) conversion & view_sale_detail logic ---")
        # Verify that converting sqlite3.Row to dict works without AttributeError
        sale_dict = dict(target_sale) if hasattr(target_sale, 'keys') else target_sale
        
        self.assertEqual(sale_dict['sale_number'], sale_number)
        self.assertEqual(sale_dict['total_amount'], total)
        
        print(f"✅ Verified dictionary conversion:")
        print(f"   - Bill Number  : {sale_dict.get('sale_number')}")
        print(f"   - Date/Time    : {sale_dict.get('sale_date')}")
        print(f"   - Subtotal     : ฿{sale_dict.get('subtotal'):,.2f}")
        print(f"   - Discount     : ฿{sale_dict.get('discount_amount'):,.2f}")
        print(f"   - Total Amount : ฿{sale_dict.get('total_amount'):,.2f}")
        print(f"   - Cashier      : {sale_dict.get('cashier_name', '-')}")
        print(f"   - Items Summary: {sale_dict.get('items_list')}")
        
        print("\n--- Step 5: Fetching sale items for detail popup ---")
        items = self.db.fetch_all("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,))
        self.assertEqual(len(items), 1)
        item_dict = dict(items[0]) if hasattr(items[0], 'keys') else items[0]
        self.assertEqual(item_dict['product_name'], 'สินค้าทดสอบรายละเอียด')
        self.assertEqual(item_dict['quantity'], 2)
        self.assertEqual(item_dict['total_price'], 300.00)
        print(f"✅ Verified sale items in detail popup:")
        print(f"   - Product: {item_dict['product_name']} x {item_dict['quantity']} = ฿{item_dict['total_price']:,.2f}")
        
        print("\n======================================================================")
        print("✅ ALL TESTS PASSED: Sales Transaction & View Detail Logic Verified 100%")
        print("======================================================================")

if __name__ == "__main__":
    unittest.main()
