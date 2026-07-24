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

def run_auto_backup():
    """ทำการสำรองข้อมูลอัตโนมัติ (Auto Backup) แบบเบื้องหลัง"""
    try:
        import zipfile
        import sqlite3
        from datetime import datetime, timedelta
        from config import DATABASE_PATH, BACKUP_DIR, PRODUCTS_IMG_DIR
        
        # 1. ตรวจสอบว่าเปิดใช้ Auto Backup หรือไม่
        db = None
        auto_enabled = True
        interval_hours = 24
        max_backups = 10
        
        try:
            db = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
            db.row_factory = sqlite3.Row
            cursor = db.cursor()
            cursor.execute("SELECT setting_key, setting_value FROM settings WHERE setting_key IN ('auto_backup', 'backup_interval_hours', 'max_backups')")
            rows = cursor.fetchall()
            settings = {row['setting_key']: row['setting_value'] for row in rows}
            
            if 'auto_backup' in settings:
                auto_enabled = settings['auto_backup'].lower() in ('true', '1')
            if 'backup_interval_hours' in settings:
                interval_hours = int(settings['backup_interval_hours'])
            if 'max_backups' in settings:
                max_backups = int(settings['max_backups'])
        except Exception:
            # ใช้ค่าจาก config / performance_config เป็นค่าเริ่มต้น
            try:
                import performance_config
                auto_enabled = performance_config.ENABLE_AUTO_BACKUP
                interval_hours = performance_config.AUTO_BACKUP_INTERVAL_HOURS
            except ImportError:
                pass
        finally:
            if db:
                db.close()
                
        if not auto_enabled:
            return
            
        # 2. ตรวจสอบความถี่ (Interval)
        # ตรวจสอบไฟล์ใน BACKUP_DIR ที่ขึ้นต้นด้วย "auto_backup_"
        if not BACKUP_DIR.exists():
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
            
        auto_backups = sorted(
            [f for f in BACKUP_DIR.glob("auto_backup_*.zip")],
            key=lambda x: x.stat().st_mtime
        )
        
        now = datetime.now()
        if auto_backups:
            latest_backup = auto_backups[-1]
            last_backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
            if now - last_backup_time < timedelta(hours=interval_hours):
                # ยังไม่ถึงเวลาสำรองข้อมูลใหม่
                return
                
        # 3. เริ่มทำการสำรองข้อมูล
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR / f"auto_backup_{timestamp}.zip"
        
        # Flush WAL
        _bk_conn = None
        try:
            _bk_conn = sqlite3.connect(str(DATABASE_PATH), timeout=15.0)
            _bk_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass
        finally:
            if _bk_conn:
                _bk_conn.close()
                
        # สร้าง ZIP
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if DATABASE_PATH.exists():
                zipf.write(str(DATABASE_PATH), "database.db")
                
            if PRODUCTS_IMG_DIR.exists():
                for img_file in PRODUCTS_IMG_DIR.glob("*"):
                    if img_file.is_file():
                        zipf.write(img_file, f"products_img/{img_file.name}")
                        
            receipt_dir = Path("data/receipts")
            if receipt_dir.exists():
                for receipt_file in receipt_dir.glob("*.pdf"):
                    zipf.write(receipt_file, f"receipts/{receipt_file.name}")
                    
        print(f"Auto backup completed: {backup_file}")
        
        # 4. ลบไฟล์สำรองเก่าที่เกินจำนวน max_backups
        auto_backups = sorted(
            [f for f in BACKUP_DIR.glob("auto_backup_*.zip")],
            key=lambda x: x.stat().st_mtime
        )
        while len(auto_backups) > max_backups:
            oldest = auto_backups.pop(0)
            try:
                oldest.unlink()
                print(f"Deleted old backup: {oldest}")
            except Exception:
                pass
                
    except Exception as e:
        print(f"Error during auto backup: {e}")

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
