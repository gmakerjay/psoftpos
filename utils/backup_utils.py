# -*- coding: utf-8 -*-
"""
ระบบ Backup ข้อมูลในรูปแบบ Markdown (Text) สำหรับสินค้า
"""

import os
from datetime import datetime
from pathlib import Path

class BackupManager:
    """จัดการการ Backup และ Import ข้อมูลสินค้าด้วย Markdown"""
    
    def __init__(self, backup_dir="Backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def export_products_to_markdown(self, products_data, filename=None):
        """
        Export รายการสินค้าเป็น Markdown Table
        products_data: list of dict
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.backup_dir / f"products_backup_{timestamp}.txt"
        else:
            filename = self.backup_dir / filename
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# รายการสินค้าสำรอง (Backup)\n")
                f.write(f"วันที่สำรองข้อมูล: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Header
                headers = ["barcode", "product_name", "category_name", "unit", "cost_price", "retail_price", "stock_quantity"]
                header_row = "| " + " | ".join(headers) + " |"
                separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
                
                f.write(header_row + "\n")
                f.write(separator_row + "\n")
                
                # Data rows
                for p in products_data:
                    row = "| " + " | ".join([str(p.get(h, "")) for h in headers]) + " |"
                    f.write(row + "\n")
                    
            return str(filename)
        except Exception as e:
            print(f"Error exporting markdown: {e}")
            return None

    def import_products_from_markdown(self, filepath):
        """
        Import รายการสินค้าจาก Markdown Table ในไฟล์ .txt
        คืนค่าเป็น list of dict
        """
        products = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            start_table = False
            headers = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("วันที่"):
                    continue
                    
                if line.startswith("|"):
                    parts = [p.strip() for p in line.split("|") if p.strip()]
                    
                    if not start_table:
                        # This is header
                        headers = parts
                        start_table = True
                        continue
                        
                    if all(p == "---" or p == ":" or p == "-:-" for p in parts):
                        # This is separator
                        continue
                        
                    # This is data row
                    if len(parts) == len(headers):
                        product = dict(zip(headers, parts))
                        # Convert types
                        try:
                            product['cost_price'] = float(product.get('cost_price', 0))
                            product['retail_price'] = float(product.get('retail_price', 0))
                            product['stock_quantity'] = int(float(product.get('stock_quantity', 0)))
                        except:
                            pass
                        products.append(product)
                        
            return products
        except Exception as e:
            print(f"Error importing markdown: {e}")
            return []

class SalesLogManager:
    """จัดการการบันทึกยอดขายลงไฟล์ .txt อย่างต่อเนื่องและระบบเคลียร์รายการ"""
    
    def __init__(self, backup_dir="Backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.current_log = self.backup_dir / "Current_Sales_Log.txt"
        
    def _get_today_str(self):
        return datetime.now().strftime("%d/%m/%Y")

    def _ensure_header(self):
        """สร้างไฟล์ใหม่พร้อมหัวไฟล์ถ้ายังไม่มี"""
        if not self.current_log.exists():
            today = self._get_today_str()
            with open(self.current_log, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write(f"ยอดขายวันที่ {today} - {today}\n")
                f.write("="*60 + "\n")
                f.write(f"{'เลขที่':<15} | {'เวลา':<10} | {'ยอดรวม':>10} | {'วิธีชำระ':<10}\n")
                f.write("-" * 60 + "\n")

    def add_sale(self, sale_data):
        """เพิ่มข้อมูลการขายลงในไฟล์"""
        self._ensure_header()
        
        # อัพเดทวันที่ในหัวไฟล์ (ถ้าวันที่เปลี่ยนแต่ยังไม่ได้กด Clear)
        # แต่ USER บอกว่า "มันจะเป็นการบันทึกต่อไปในไฟล์เดิม" จนกว่าจะกด Clear
        # ดังนั้นจะไม่อัพเดทหัวไฟล์ แต่จะบันทึกรายการต่อท้าย
        
        try:
            with open(self.current_log, 'a', encoding='utf-8') as f:
                time_str = datetime.now().strftime("%H:%M:%S")
                line = f"{sale_data['sale_number']:<15} | {time_str:<10} | {sale_data['total_amount']:>10,.2f} | {sale_data['payment_method']:<10}\n"
                f.write(line)
            return True
        except Exception as e:
            print(f"Error adding sale to log: {e}")
            return False

    def clear_and_rotate(self):
        """เคลียร์รายการ: เปลี่ยนชื่อไฟล์เดิมตามช่วงวันที่ และเริ่มไฟล์ใหม่"""
        if not self.current_log.exists():
            return False
            
        try:
            # อ่านหัวไฟล์เพื่อหาวันที่เริ่มต้น
            with open(self.current_log, 'r', encoding='utf-8') as f:
                header = f.readlines()[1] # บรรทัดที่ 2 คือ ยอดขายวันที่ xx - xx
            
            # ดึงวันที่จาก header "ยอดขายวันที่ 04/02/2026 - 04/02/2026"
            date_part = header.replace("ยอดขายวันที่", "").strip()
            # แทนที่ / ด้วย - เพื่อตั้งชื่อไฟล์
            safe_date = date_part.replace("/", "-").replace(" ", "")
            
            timestamp = datetime.now().strftime("%H%M%S")
            new_name = self.backup_dir / f"Sales_Summary_{safe_date}_{timestamp}.txt"
            
            # เปลี่ยนชื่อไฟล์
            self.current_log.rename(new_name)
            
            # สร้างไฟล์ใหม่ทันที
            self._ensure_header()
            return str(new_name)
        except Exception as e:
            print(f"Error rotating sales log: {e}")
            return False

    def get_current_log_content(self):
        """ดึงเนื้อหาในไฟล์ปัจจุบัน"""
        if not self.current_log.exists():
            return "ยังไม่มีข้อมูลการขาย"
        try:
            with open(self.current_log, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "ไม่สามารถอ่านข้อมูลได้"

if __name__ == "__main__":
    # Test
    bm = BackupManager()
    # ... (existing test) ...
    
    slm = SalesLogManager()
    slm.add_sale({
        "sale_number": "SL202402040001",
        "total_amount": 1500.50,
        "payment_method": "เงินสด"
    })
    print("Log Content:")
    print(slm.get_current_log_content())
