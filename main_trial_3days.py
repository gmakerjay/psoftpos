# -*- coding: utf-8 -*-
"""
โปรแกรมขายหน้าร้าน (Point of Sale System) - เวอร์ชันทดลองใช้ 3 วัน
"""

import sys
import os

# เพิ่ม path สำหรับ import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ทำการ Override ระบบ License ด้วยระบบทดลองใช้งาน (3-Day Trial) เพื่อป้องกันผลกระทบกับโค้ดหลัก
try:
    import utils.license_system_trial_3days as license_system_trial_3days
    sys.modules['utils.license_system'] = license_system_trial_3days
except Exception as e:
    print(f"Error overriding license system for 3-day trial version: {e}")

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
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
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

def register_process_font():
    """ลงทะเบียนฟอนต์ภาษาไทยสำหรับ Windows GDI ทั่วทั้งโปรแกรม"""
    try:
        import platform
        if platform.system() == 'Windows':
            import ctypes
            base_path = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(base_path, "FC Sara Samkan [Non-commercial] Bold.ttf")
            if os.path.exists(font_path):
                res = ctypes.windll.gdi32.AddFontResourceW(font_path)
                if res > 0:
                    print(f"Registered GDI Font resource: {font_path} (result: {res})")
                    try:
                        import win32con
                        import win32gui
                        win32gui.PostMessage(win32con.HWND_BROADCAST, win32con.WM_FONTCHANGE, 0, 0)
                    except Exception:
                        pass
    except Exception as e:
        print(f"Failed to register process font: {e}")

def cleanup_resources():
    """ทำความสะอาดคืนทรัพยากร ปิดการเชื่อมต่อฐานข้อมูล ปิดไฟล์ Log ยกเลิกฟอนต์ และย้าย Working Directory เพื่อปลดล็อกโฟลเดอร์บน Windows"""
    try:
        from database.db_manager import DatabaseManager
        DatabaseManager.close_all_connections()
    except Exception:
        pass
    try:
        import platform
        if platform.system() == 'Windows':
            import ctypes
            base_path = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(base_path, "FC Sara Samkan [Non-commercial] Bold.ttf")
            if os.path.exists(font_path):
                ctypes.windll.gdi32.RemoveFontResourceW(font_path)
    except Exception:
        pass
    try:
        import logging
        logging.shutdown()
    except Exception:
        pass
    try:
        import os
        os.chdir(os.path.expanduser("~"))
    except Exception:
        pass

def main():
    """ฟังก์ชันหลักของโปรแกรม"""
    try:
        ensure_directories()
        register_process_font()
        logger.info("Starting POS System (3-Day Trial Version)...")
        
        # === รัน Auto Backup ในพื้นหลัง ===
        try:
            import threading
            from utils import run_auto_backup
            threading.Thread(target=run_auto_backup, daemon=True).start()
            logger.info("Background Auto Backup thread started.")
        except Exception as e:
            logger.error(f"Failed to start auto backup: {e}")
        
        # ตรวจสอบ Activation ก่อน
        logger.info("🔐 Checking activation status...")
        is_activated, message, license_data = LicenseManager.check_activation()
        
        if not is_activated:
            logger.warning(f"❌ โปรแกรมทดลองหมดอายุการใช้งาน: {message}")
            print(f"Trial expired: {message}")
            
            root = ctk.CTk()
            root.withdraw()
            
            from tkinter import messagebox as mb
            mb.showerror("เวอร์ชันทดลองหมดอายุแล้ว", f"{message}\n\nกรุณาติดต่อผู้ขายเพื่อลงทะเบียนเปิดใช้งานเต็มรูปแบบ")
            root.destroy()
            sys.exit(0)
        else:
            logger.info(f"✅ โปรแกรมเวอร์ชันทดลองกำลังทำงาน")
            logger.info(f"📅 วันหมดอายุ: {license_data.get('expire_date', 'N/A')} (คงเหลือ {license_data.get('days_left', 0)} วัน)")
            print(f"Program activated in 3-Day Trial Mode")
            print(f"Expiry: {license_data.get('expire_date', 'N/A')} ({license_data.get('days_left', 0)} days left)")
        
        # === ตรวจสอบ License ใกล้หมดอายุ ===
        if is_activated and license_data:
            warning_info = LicenseManager.get_expiry_warning(license_data)
            
            if warning_info and warning_info['level'] != 'none':
                from tkinter import messagebox as mb
                import customtkinter as _ctk
                
                _root = _ctk.CTk()
                _root.withdraw()
                
                level = warning_info['level']
                title = warning_info['title']
                message = warning_info['message']
                
                logger.warning(f"⚠️ License Warning: {warning_info['level']} - เหลือ {warning_info['days_left']} วัน")
                
                if level == 'expired':
                    mb.showerror(title, message, parent=_root)
                    logger.warning("❌ License หมดอายุ - ปิดโปรแกรม")
                    _root.destroy()
                    sys.exit(0)
                elif level == 'critical':
                    mb.showwarning(title, message, parent=_root)
                else:
                    mb.showinfo(title, message, parent=_root)
                    
                _root.destroy()
        
        # แสดงหน้า Login
        logger.info("Opening login window...")
        login_app = LoginWindow()
        user_id, user_info = login_app.run()
        
        if user_id and user_info:
            full_name = user_info['full_name'] if 'full_name' in user_info.keys() else 'Unknown'
            log_user_action(user_id, "LOGIN", f"User: {full_name} (3-Day Trial Version)")
            logger.info(f"User {user_id} logged in: {full_name} (3-Day Trial Version)")
            
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
    finally:
        cleanup_resources()


if __name__ == "__main__":
    main()
