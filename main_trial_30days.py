# -*- coding: utf-8 -*-
"""
โปรแกรมขายหน้าร้าน (Point of Sale System) - เวอร์ชันทดลองใช้ 30 วัน (1 เดือน)

ฟีเจอร์พิเศษ:
  - ทดลองใช้ได้ 30 วัน (ฟีเจอร์ทุกอย่างใช้ได้ครบ เหมือนเวอร์ชันเต็มทุกประการ)
  - หมดอายุแล้ว DB ยังคงอยู่ ข้อมูลไม่หาย
  - Backup ยังทำงานได้ปกติแม้หมดอายุ
  - ลบลงใหม่ก็ใช้ซ้ำไม่ได้ (เก็บ trial ใน Windows Registry)
  - ลูกค้าซื้อจริงแล้วนำ DB เก่ากลับมาใช้ได้
"""

import sys
import os

# เพิ่ม path สำหรับ import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ทำการ Override ระบบ License ด้วยระบบทดลองใช้งาน (30-Day Trial)
# เพื่อป้องกันผลกระทบกับโค้ดหลัก — แค่เปลี่ยนวิธีตรวจ License เท่านั้น
try:
    import utils.license_system_trial_30days as license_system_trial_30days
    sys.modules['utils.license_system'] = license_system_trial_30days
except Exception as e:
    print(f"Error overriding license system for 30-day trial version: {e}")

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
        base_path = os.path.dirname(sys.executable)
    else:
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
        print(f"Error registering font: {e}")

def run_backup_on_expiry():
    """รัน Auto Backup เมื่อโปรแกรมหมดอายุ — เพื่อให้ลูกค้ามั่นใจว่าข้อมูลไม่หาย"""
    try:
        from utils import run_auto_backup
        run_auto_backup()
        logger.info("✅ Auto Backup completed before trial expiry notification.")
    except Exception as e:
        logger.error(f"⚠️ Backup on expiry failed: {e}")



def main():
    """ฟังก์ชันหลักของโปรแกรม (เปิดโปรแกรมได้ทันทีภายใน 1.5 วินาที)"""
    try:
        ensure_directories()
        register_process_font()
        logger.info("Starting POS System (30-Day Trial Version)...")

        # ตรวจสอบ Activation ก่อน (0.008 วินาที)
        is_activated, message, license_data = LicenseManager.check_activation()

        if not is_activated:
            logger.warning(f"❌ โปรแกรมทดลองหมดอายุการใช้งาน: {message}")
            print(f"Trial expired: {message}")
            run_backup_on_expiry()
            expired_window = ExpiredModeWindow(license_data)
            expired_window.run()
            sys.exit(0)

        # เตรียมฐานข้อมูล (แบบรวดเร็ว 0.005 วินาที)
        try:
            from database import DatabaseManager
            db_mgr = DatabaseManager()
            db_mgr.initialize_database()
        except Exception as e:
            logger.error(f"Database init warning: {e}")

        # รัน Auto Backup ในพื้นหลังหลังจากเปิดหน้าต่าง Login
        try:
            import threading
            from utils import run_auto_backup
            threading.Thread(target=run_auto_backup, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start auto backup: {e}")

        # ตรวจสอบ License ใกล้หมดอายุ
        if is_activated and license_data:
            warning_info = LicenseManager.get_expiry_warning(license_data)
            if warning_info and warning_info['level'] != 'none':
                from tkinter import messagebox as mb
                _root = ctk.CTk()
                _root.withdraw()
                level = warning_info['level']
                title = warning_info['title']
                msg = warning_info['message']
                if level == 'expired':
                    mb.showerror(title, msg, parent=_root)
                    _root.destroy()
                    sys.exit(0)
                elif level == 'critical':
                    mb.showwarning(title, msg, parent=_root)
                else:
                    mb.showinfo(title, msg, parent=_root)
                _root.destroy()

        # เปิดหน้า Login ทันที! (1.5 วินาที)
        logger.info("Opening login window...")
        login_app = LoginWindow(license_data)
        user_id, user_info = login_app.run()

        if user_id and user_info:
            full_name = user_info['full_name'] if 'full_name' in user_info.keys() else 'Unknown'
            log_user_action(user_id, "LOGIN", f"User: {full_name} (30-Day Trial Version)")
            logger.info(f"User {user_id} logged in: {full_name} (30-Day Trial Version)")
            
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



class ExpiredModeWindow:
    """หน้าต่างโหมดหมดอายุ — ลูกค้าสามารถเข้ามาสำรองข้อมูลได้ตลอดเวลา
    
    ฟีเจอร์:
    - สำรองข้อมูลทั้งหมด (DB + รูปสินค้า + Backup เก่า) เป็น ZIP
    - คัดลอกเฉพาะฐานข้อมูลออกมา
    - เปิดโฟลเดอร์ data/ ให้คัดลอกเอง
    - กดสำรองได้ไม่จำกัดจำนวนครั้ง
    """
    
    def __init__(self, license_data=None):
        self.license_data = license_data or {}
        self.root = None
    
    def run(self):
        self.root = ctk.CTk()
        self.root.title("StorePOS - เวอร์ชันทดลองหมดอายุ")
        self.root.geometry("620x620")
        self.root.resizable(False, False)
        
        # ตั้ง icon
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(os.path.dirname(sys.executable), "icon.ico")
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # === หัวข้อ ===
        header_frame = ctk.CTkFrame(self.root, fg_color="#dc3545", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame,
            text="⛔ เวอร์ชันทดลอง 30 วันหมดอายุแล้ว",
            font=("Sarabun", 22, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        # === ข้อมูลหมดอายุ ===
        info_frame = ctk.CTkFrame(self.root)
        info_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        expire_date = self.license_data.get('expire_date', 'ไม่ทราบ')
        ctk.CTkLabel(
            info_frame,
            text=f"📅  วันหมดอายุ: {expire_date}",
            font=("Sarabun", 15),
            anchor="w"
        ).pack(padx=15, pady=(10, 2), anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text="📦  ข้อมูลสินค้าและการขายของท่านยังคงอยู่ครบถ้วนในฐานข้อมูล",
            font=("Sarabun", 15, "bold"),
            text_color="#28a745",
            anchor="w"
        ).pack(padx=15, pady=2, anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text="💾  ท่านสามารถสำรองข้อมูลได้ตลอดเวลา ไม่จำกัดจำนวนครั้ง",
            font=("Sarabun", 15),
            anchor="w"
        ).pack(padx=15, pady=2, anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text="🔄  ใส่ License Key เพื่อใช้งานต่อได้ทันที ข้อมูลเดิมไม่หาย",
            font=("Sarabun", 15),
            anchor="w"
        ).pack(padx=15, pady=(2, 10), anchor="w")
        
        # === ปุ่มจัดการและสำรองข้อมูล ===
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔑  เปิดใช้งาน License Key (ปลดล็อกเวอร์ชันเต็ม)",
            font=("Sarabun", 16, "bold"),
            height=48,
            fg_color="#0d6efd",
            hover_color="#0b5ed7",
            command=self._activate_license_key
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            btn_frame,
            text="📦  สำรองข้อมูลทั้งหมด (ZIP)",
            font=("Sarabun", 16, "bold"),
            height=45,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._backup_all_zip
        ).pack(fill="x", pady=4)
        
        ctk.CTkButton(
            btn_frame,
            text="💾  คัดลอกเฉพาะฐานข้อมูล (database.db)",
            font=("Sarabun", 16, "bold"),
            height=45,
            fg_color="#17a2b8",
            hover_color="#138496",
            command=self._backup_db_only
        ).pack(fill="x", pady=4)
        
        ctk.CTkButton(
            btn_frame,
            text="📂  เปิดโฟลเดอร์ข้อมูล (data/)",
            font=("Sarabun", 16, "bold"),
            height=45,
            fg_color="#6c757d",
            hover_color="#5a6268",
            command=self._open_data_folder
        ).pack(fill="x", pady=4)
        
        # === ปุ่มปิดโปรแกรม ===
        ctk.CTkButton(
            self.root,
            text="❌  ปิดโปรแกรม",
            font=("Sarabun", 14),
            height=38,
            fg_color="#dc3545",
            hover_color="#c82333",
            command=self.root.destroy
        ).pack(pady=(8, 4))
        
        # === ข้อความติดต่อ ===
        ctk.CTkLabel(
            self.root,
            text="กรุณาติดต่อผู้ขายเพื่อสั่งซื้อสิทธิ์การใช้งานเต็มรูปแบบ",
            font=("Sarabun", 13),
            text_color="gray"
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            self.root,
            text="⚠️ การลบโปรแกรมแล้วลงใหม่จะไม่สามารถทดลองใช้ซ้ำได้",
            font=("Sarabun", 12),
            text_color="#dc3545"
        ).pack(pady=(0, 10))
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        try:
            from database.db_manager import DatabaseManager
            DatabaseManager.close_all_connections()
        except Exception:
            pass
        if self.root:
            try:
                self.root.destroy()
            except:
                pass
        sys.exit(0)
    
    def _get_base_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    
    def _activate_license_key(self):
        """เปิดหน้าต่างกรอก License Key เพื่อเปิดใช้งานเวอร์ชันเต็ม"""
        try:
            from ui.activation_window import ActivationWindow
            def on_activate_success():
                from tkinter import messagebox as mb
                mb.showinfo(
                    "ปลดล็อกสำเร็จ 🎉",
                    "ระบบได้รับการเปิดใช้งานเป็นเวอร์ชันเต็มเรียบร้อยแล้ว!\n"
                    "ข้อมูลสินค้า ประวัติการขาย และสต็อกเดิมทั้งหมดพร้อมใช้งานต่อได้ทันที\n\n"
                    "โปรแกรมจะเริ่มทำงานใหม่ในโหมดเวอร์ชันเต็ม",
                    parent=self.root
                )
                self.root.destroy()
                # รีสตาร์ทโปรแกรมเข้าโหมดปกติ
                restart_application()

            act_win = ActivationWindow(self.root, on_success=on_activate_success)
        except Exception as e:
            logger.error(f"Error launching activation window: {e}")
            from tkinter import messagebox as mb
            mb.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าต่างลงทะเบียนได้: {e}", parent=self.root)
    
    def _backup_all_zip(self):
        """สำรองข้อมูลทั้งหมดเป็น ZIP (DB + รูปสินค้า + Backup เก่า)"""
        from tkinter import filedialog, messagebox as mb
        import zipfile
        from datetime import datetime as dt
        
        try:
            save_path = filedialog.askdirectory(
                title="เลือกโฟลเดอร์สำหรับสำรองข้อมูล",
                parent=self.root
            )
            if not save_path:
                return
            
            base = self._get_base_path()
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(save_path, f"StorePOS_Backup_{timestamp}.zip")
            
            file_count = 0
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # ฐานข้อมูลหลัก
                db_path = os.path.join(base, "data", "database.db")
                if os.path.exists(db_path):
                    zipf.write(db_path, "database.db")
                    file_count += 1
                
                # รูปสินค้า
                img_dir = os.path.join(base, "data", "products")
                if os.path.exists(img_dir):
                    for f in os.listdir(img_dir):
                        fpath = os.path.join(img_dir, f)
                        if os.path.isfile(fpath):
                            zipf.write(fpath, f"products/{f}")
                            file_count += 1
                
                # โฟลเดอร์ Backup
                bk_dir = os.path.join(base, "Backup")
                if os.path.exists(bk_dir):
                    for f in os.listdir(bk_dir):
                        fpath = os.path.join(bk_dir, f)
                        if os.path.isfile(fpath):
                            zipf.write(fpath, f"Backup/{f}")
                            file_count += 1
                
                # Excel Exports
                excel_dir = os.path.join(base, "Excel_Exports")
                if os.path.exists(excel_dir):
                    for f in os.listdir(excel_dir):
                        fpath = os.path.join(excel_dir, f)
                        if os.path.isfile(fpath):
                            zipf.write(fpath, f"Excel_Exports/{f}")
                            file_count += 1
            
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)
            mb.showinfo(
                "สำรองข้อมูลสำเร็จ ✅",
                f"ข้อมูลทั้งหมดถูกสำรองเรียบร้อย!\n\n"
                f"📁 ไฟล์: {backup_file}\n"
                f"📊 จำนวนไฟล์: {file_count} ไฟล์\n"
                f"💾 ขนาด: {size_mb:.1f} MB\n\n"
                f"📦 ไฟล์นี้สามารถนำกลับมาใช้ได้เมื่อซื้อเวอร์ชันเต็ม",
                parent=self.root
            )
            logger.info(f"✅ Full backup saved: {backup_file} ({file_count} files, {size_mb:.1f}MB)")
            
        except Exception as e:
            logger.error(f"Backup error: {e}")
            mb.showerror("สำรองข้อมูลไม่สำเร็จ", f"เกิดข้อผิดพลาด: {e}", parent=self.root)
    
    def _backup_db_only(self):
        """คัดลอกเฉพาะไฟล์ฐานข้อมูล"""
        from tkinter import filedialog, messagebox as mb
        import shutil
        from datetime import datetime as dt
        
        try:
            base = self._get_base_path()
            db_path = os.path.join(base, "data", "database.db")
            
            if not os.path.exists(db_path):
                mb.showwarning("ไม่พบฐานข้อมูล", "ไม่พบไฟล์ database.db ในโฟลเดอร์ data/", parent=self.root)
                return
            
            timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
            save_file = filedialog.asksaveasfilename(
                title="บันทึกฐานข้อมูล",
                defaultextension=".db",
                initialfile=f"database_backup_{timestamp}.db",
                filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
                parent=self.root
            )
            if not save_file:
                return
            
            shutil.copy2(db_path, save_file)
            size_mb = os.path.getsize(save_file) / (1024 * 1024)
            
            mb.showinfo(
                "คัดลอกฐานข้อมูลสำเร็จ ✅",
                f"ฐานข้อมูลถูกคัดลอกเรียบร้อย!\n\n"
                f"📁 ไฟล์: {save_file}\n"
                f"💾 ขนาด: {size_mb:.1f} MB\n\n"
                f"📦 ไฟล์นี้สามารถนำกลับมาใช้ได้เมื่อซื้อเวอร์ชันเต็ม",
                parent=self.root
            )
            logger.info(f"✅ DB backup saved: {save_file} ({size_mb:.1f}MB)")
            
        except Exception as e:
            logger.error(f"DB backup error: {e}")
            mb.showerror("คัดลอกฐานข้อมูลไม่สำเร็จ", f"เกิดข้อผิดพลาด: {e}", parent=self.root)
    
    def _open_data_folder(self):
        """เปิดโฟลเดอร์ data/ ใน File Explorer"""
        try:
            base = self._get_base_path()
            data_dir = os.path.join(base, "data")
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            os.startfile(data_dir)
            logger.info(f"📂 Opened data folder: {data_dir}")
        except Exception as e:
            logger.error(f"Open folder error: {e}")
            from tkinter import messagebox as mb
            mb.showerror("เปิดโฟลเดอร์ไม่สำเร็จ", f"เกิดข้อผิดพลาด: {e}", parent=self.root)


if __name__ == "__main__":
    main()
