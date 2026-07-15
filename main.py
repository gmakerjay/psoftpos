# -*- coding: utf-8 -*-
"""
โปรแกรมขายหน้าร้าน (Point of Sale System)
เวอร์ชัน 1.0.0

โปรแกรมจัดการร้านค้าครบวงจร
- ขายสินค้า
- จัดการสต็อก
- รายงานและสถิติ
- พิมพ์ใบเสร็จ
- ระบบบาร์โค้ด
- และอื่นๆ อีกมากมาย
"""

import sys
import os

# เพิ่ม path สำหรับ import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui import LoginWindow, MainWindow
from ui.activation_window import ActivationWindow
from utils.license_system import LicenseManager
from utils.logger import get_logger, log_info, log_error, log_user_action, new_log_session
from config import *
import customtkinter as ctk

# สร้าง Logger
logger = get_logger(__name__)


def ensure_directories():
    """สร้างโครงสร้างโฟลเดอร์ที่จำเป็นเพื่อป้องกัน Error"""
    # ตรวจสอบว่าทำงานจาก .exe หรือไม่
    if getattr(sys, 'frozen', False):
        # ถ้าทำงานจาก .exe ใช้ path ของ .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # ถ้าทำงานจาก Python ปกติ ใช้ path ของ script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # เปลี่ยน working directory ไปยัง base_path
    os.chdir(base_path)
    
    dirs = [
        "data",
        "data/products",
        "data/backups",
        "Backup",
        "Logs",
        "Excel_Exports",
        "assets"
    ]
    for d in dirs:
        dir_path = os.path.join(base_path, d)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Checked/Created directory: {dir_path}")

def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    try:
        ensure_directories()
        logger.info("Starting POS System...")
        
        # ===== BYPASS ACTIVATION (สำหรับทดสอบ) =====
        logger.warning("BYPASS MODE: Skip activation check")
        print("BYPASS MODE: Test program without activation")
        
        # TODO: ลบ comment ด้านล่างเมื่อต้องการเปิดใช้งาน Activation จริง
        """
        # ตรวจสอบ Activation ก่อน
        logger.info("🔐 Checking activation status...")
        is_activated, message, license_data = LicenseManager.check_activation()
        
        if not is_activated:
            logger.warning(f"❌ โปรแกรมยังไม่ได้ Activate: {message}")
            print(f"Program not activated: {message}")
            
            # สร้าง root window ชั่วคราว
            root = ctk.CTk()
            root.withdraw()
            
            # แสดงหน้า Activation
            logger.info("🔑 Opening activation window...")
            activation_window = ActivationWindow(root, on_success=lambda: logger.info("✅ Activation สำเร็จ!"))
            root.wait_window(activation_window)
            
            # ตรวจสอบอีกครั้งหลัง Activate
            is_activated, message, license_data = LicenseManager.check_activation()
            root.destroy()
            
            if not is_activated:
                logger.warning("❌ ยกเลิกการใช้งาน - ไม่มี Activation")
                print("Exit - No Activation")
                sys.exit(0)
        else:
            logger.info(f"✅ โปรแกรมได้รับการ Activate แล้ว")
            logger.info(f"📅 หมดอายุ: {license_data.get('expire_date', 'N/A')}")
            print(f"Program activated")
            print(f"Expiry: {license_data.get('expire_date', 'N/A')}")
        """
        
        # แสดงหน้า Login
        logger.info("Opening login window...")
        login_app = LoginWindow()
        user_id, user_info = login_app.run()
        
        # ถ้า login สำเร็จ เปิดหน้าหลัก
        if user_id and user_info:
            full_name = user_info['full_name'] if 'full_name' in user_info.keys() else 'Unknown'
            log_user_action(user_id, "LOGIN", f"User: {full_name}")
            logger.info(f"User {user_id} logged in: {full_name}")
            
            # เริ่ม Session ใหม่
            new_log_session("USER_LOGIN")
            
            main_app = MainWindow(user_id, user_info)
            main_app.run()
            
            logger.info(f"User {user_id} logged out")
        else:
            logger.info("Cancelled - No Login")
            print("Cancelled - No Login")
        
        logger.info("POS System Stopped")
        logger.info("="*70)
            
    except KeyboardInterrupt:
        logger.info("\nProgram cancelled by user (Ctrl+C)")
        print("\nProgram cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Critical Error: {e}", exc_info=True)
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
