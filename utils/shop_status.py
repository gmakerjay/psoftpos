# -*- coding: utf-8 -*-
"""
Shop Status Manager - จัดการสถานะเปิด/ปิดร้าน
"""

from database import DatabaseManager
from datetime import datetime
from utils.logger import get_logger, new_log_session

logger = get_logger(__name__)


class ShopStatusManager:
    """จัดการสถานะร้าน"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def is_shop_open(self):
        """ตรวจสอบว่าร้านเปิดอยู่หรือไม่"""
        self.db.connect()
        status = self.db.fetch_one(
            "SELECT setting_value FROM settings WHERE setting_key = 'shop_status'"
        )
        self.db.disconnect()
        
        if status:
            return status['setting_value'] == 'open'
        return True  # Default: เปิด
    
    def open_shop(self, user_id):
        """เปิดร้าน"""
        self.db.connect()
        
        # บันทึกสถานะ
        self.db.execute("""
            INSERT INTO settings (setting_key, setting_value)
            VALUES ('shop_status', 'open')
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = 'open'
        """)
        
        # บันทึก log
        self.db.execute("""
            INSERT INTO shop_status_log (user_id, action, action_time)
            VALUES (?, 'open', ?)
        """, (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.db.disconnect()
        
        # บันทึก log และเริ่ม session ใหม่
        logger.info(f"🏪 ร้านเปิดแล้ว - User ID: {user_id}")
        new_log_session("SHOP_OPEN")
        
        return True
    
    def close_shop(self, user_id):
        """ปิดร้าน"""
        # ดึงสรุปยอดขายก่อนปิดร้าน
        summary = self.get_today_summary()
        
        self.db.connect()
        
        # บันทึกสถานะ
        self.db.execute("""
            INSERT INTO settings (setting_key, setting_value)
            VALUES ('shop_status', 'closed')
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = 'closed'
        """)
        
        # บันทึก log
        self.db.execute("""
            INSERT INTO shop_status_log (user_id, action, action_time)
            VALUES (?, 'close', ?)
        """, (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.db.disconnect()
        
        # บันทึก log พร้อมสรุปยอดขาย
        logger.info(f"🏪 ร้านปิดแล้ว - User ID: {user_id}")
        logger.info(f"📊 สรุปยอดขายวันนี้:")
        logger.info(f"   💰 ยอดขายรวม: ฿{summary.get('total_revenue', 0):,.2f}")
        logger.info(f"   📝 จำนวนบิล: {summary.get('total_sales', 0)} บิล")
        logger.info(f"   🎁 ส่วนลด: ฿{summary.get('total_discount', 0):,.2f}")
        new_log_session("SHOP_CLOSE")
        
        return True
    
    def get_today_summary(self):
        """สรุปยอดขายวันนี้"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.db.connect()
        summary = self.db.fetch_one(f"""
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                SUM(discount_amount) as total_discount
            FROM sales
            WHERE DATE(sale_date) = '{today}'
            AND status = 'completed'
        """)
        self.db.disconnect()
        
        return summary if summary else {
            'total_sales': 0,
            'total_revenue': 0,
            'total_discount': 0
        }
    
    def create_shop_status_table(self):
        """สร้างตาราง shop_status_log ถ้ายังไม่มี"""
        self.db.connect()
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS shop_status_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                action_time TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.db.disconnect()


# สร้างตารางตอน import
try:
    manager = ShopStatusManager()
    manager.create_shop_status_table()
except:
    pass
