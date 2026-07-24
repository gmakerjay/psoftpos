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

from ui import LoginWindow, MainWindow, SplashScreen
from ui.activation_window import ActivationWindow
from utils.license_system import LicenseManager
from utils.system_utils import cleanup_resources, restart_application
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



def safe_exit(code=0):
    """ทำความสะอาดคืนทรัพยากร และบังคับปิดโปรแกรมระดับ OS เพื่อป้องกัน Process ค้าง"""
    try:
        cleanup_resources()
    except Exception:
        pass
    import os
    os._exit(code)


def main():
    """ฟังก์ชันหลักของโปรแกรม (Multi-threaded Edition สำหรับคอมพิวเตอร์รุ่นเก่า)"""
    try:
        splash = SplashScreen("StorePOS", "ระบบจัดการร้านค้าและขายหน้าร้าน")
        
        def task_dirs():
            ensure_directories()
            
        def task_font():
            register_process_font()
            
        def task_backup():
            try:
                import threading
                from utils import run_auto_backup
                threading.Thread(target=run_auto_backup, daemon=True).start()
            except Exception as e:
                logger.error(f"Failed to start auto backup: {e}")
                
        def task_lic():
            return LicenseManager.check_activation()
            
        def task_db():
            from database import DatabaseManager
            db_mgr = DatabaseManager()
            db_mgr.initialize_database()

        tasks = [
            ("dirs", "กำลังตรวจสอบโครงสร้างโฟลเดอร์...", task_dirs),
            ("font", "กำลังลงทะเบียนฟอนต์ภาษาไทย...", task_font),
            ("license", "🔐 กำลังตรวจสอบสิทธิ์การใช้งาน (License)...", task_lic),
            ("db", "💾 กำลังเตรียมฐานข้อมูลและโครงสร้างระบบ...", task_db),
            ("backup", "กำลังเริ่มต้นระบบ Auto Backup ในพื้นหลัง...", task_backup),
        ]

        def on_loading_complete(results):
            lic_res = results.get("license")
            if lic_res and isinstance(lic_res, tuple):
                is_activated, message, license_data = lic_res
            else:
                is_activated, message, license_data = False, "Unknown license status", None

            if not is_activated:
                logger.warning(f"❌ โปรแกรมยังไม่ได้ Activate: {message}")
                print(f"Program not activated: {message}")
                
                root = ctk.CTk()
                root.withdraw()
                logger.info("🔑 Opening activation window...")
                activation_window = ActivationWindow(root, on_success=lambda: logger.info("✅ Activation สำเร็จ!"))
                root.wait_window(activation_window)
                
                is_activated, message, license_data = LicenseManager.check_activation()
                root.destroy()
                
                if not is_activated:
                    logger.warning("❌ ยกเลิกการใช้งาน - ไม่มี Activation")
                    print("Exit - No Activation")
                    safe_exit(0)
            else:
                logger.info(f"✅ โปรแกรมได้รับการ Activate แล้ว")
                logger.info(f"📅 หมดอายุ: {license_data.get('expire_date', 'N/A')}")
                print(f"Program activated")

            # ตรวจสอบ License ใกล้หมดอายุ
            if is_activated and license_data:
                warning_info = LicenseManager.get_expiry_warning(license_data)
                if warning_info and warning_info['level'] != 'none':
                    from tkinter import messagebox as mb
                    import customtkinter as _ctk
                    _root = _ctk.CTk()
                    _root.withdraw()
                    level = warning_info['level']
                    title = warning_info['title']
                    msg = warning_info['message']
                    if level == 'expired':
                        mb.showerror(title, msg, parent=_root)
                        _root.destroy()
                        safe_exit(0)
                    elif level == 'critical':
                        mb.showwarning(title, msg, parent=_root)
                    else:
                        mb.showinfo(title, msg, parent=_root)
                    _root.destroy()

            # แสดงหน้า Login
            logger.info("Opening login window...")
            login_app = LoginWindow(license_data)
            user_id, user_info = login_app.run()

            
            if user_id and user_info:
                full_name = user_info['full_name'] if 'full_name' in user_info.keys() else 'Unknown'
                log_user_action(user_id, "LOGIN", f"User: {full_name}")
                logger.info(f"User {user_id} logged in: {full_name}")
                
                new_log_session("USER_LOGIN")
                
                main_app = MainWindow(user_id, user_info)
                main_app.run()
                
                logger.info(f"User {user_id} logged out")
            else:
                logger.info("Cancelled - No Login")
                print("Cancelled - No Login")
            
            logger.info("POS System Stopped")
            logger.info("="*70)
            safe_exit(0)

        splash.run_tasks_threaded(tasks, on_loading_complete)
    except KeyboardInterrupt:
        logger.info("\nProgram cancelled by user (Ctrl+C)")
        print("\nProgram cancelled by user")
        safe_exit(0)
    except Exception as e:
        logger.critical(f"Critical Error: {e}", exc_info=True)
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        safe_exit(1)
    finally:
        safe_exit(0)



if __name__ == "__main__":
    main()
