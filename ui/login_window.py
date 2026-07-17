# -*- coding: utf-8 -*-
"""
หน้า Login
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
import sys


class LoginWindow:
    """หน้าล็อกอินเข้าสู่ระบบ"""
    
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title(f"{APP_NAME} - เข้าสู่ระบบ")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        
        # ตั้งค่าไอคอนหน้าต่าง
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Error loading icon: {e}")
        
        # ตั้งค่าธีม
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # ตัวแปร
        self.db = DatabaseManager()
        self.user_id = None
        self.user_info = None
        
        # สร้าง UI
        self.create_widgets()
        
        # วางหน้าต่างกลางจอ
        self.center_window()
        
    def center_window(self):
        """วางหน้าต่างกลางจอ"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """สร้าง UI"""
        # Container หลัก
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # โลโก้/ชื่อโปรแกรม
        logo_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["primary"], corner_radius=15)
        logo_frame.pack(pady=(0, 30), fill="x")
        
        title_label = ctk.CTkLabel(
            logo_frame,
            text="🏪 " + APP_NAME,
            font=FONTS["title"],
            text_color="white"
        )
        title_label.pack(pady=20)
        
        subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="ระบบจัดการร้านค้าครบวงจร",
            font=FONTS["body"],
            text_color="white"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # ตรวจสอบสิทธิ์ว่ามีข้อมูลทดลองใช้งานหรือไม่
        trial_info_text = None
        try:
            from utils.license_system import LicenseManager
            is_val, msg, lic_data = LicenseManager.check_activation()
            if lic_data and lic_data.get('is_trial'):
                days_left = lic_data.get('days_left', 0)
                trial_info_text = f"⚠️ เวอร์ชันทดลองใช้งาน (คงเหลือ {days_left} วัน)"
        except Exception:
            pass

        if trial_info_text:
            trial_badge = ctk.CTkLabel(
                logo_frame,
                text=trial_info_text,
                font=("Sarabun", 13, "bold"),
                text_color="#FFEB3B"
            )
            trial_badge.pack(pady=(0, 15))
            
        # ฟอร์มล็อกอิน
        login_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=15)
        login_frame.pack(fill="both", expand=True)
        
        # หัวข้อ
        login_title = ctk.CTkLabel(
            login_frame,
            text="เข้าสู่ระบบ",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        )
        login_title.pack(pady=(30, 20))
        
        # ชื่อผู้ใช้
        username_label = ctk.CTkLabel(
            login_frame,
            text="ชื่อผู้ใช้",
            font=FONTS["body"],
            text_color=COLORS["text_dark"]
        )
        username_label.pack(pady=(20, 5), anchor="w", padx=40)
        
        self.username_entry = ctk.CTkEntry(
            login_frame,
            height=45,
            font=FONTS["body"],
            placeholder_text="กรอกชื่อผู้ใช้"
        )
        self.username_entry.pack(pady=(0, 15), padx=40, fill="x")
        
        # รหัสผ่าน
        password_label = ctk.CTkLabel(
            login_frame,
            text="รหัสผ่าน",
            font=FONTS["body"],
            text_color=COLORS["text_dark"]
        )
        password_label.pack(pady=(0, 5), anchor="w", padx=40)
        
        self.password_entry = ctk.CTkEntry(
            login_frame,
            height=45,
            font=FONTS["body"],
            placeholder_text="กรอกรหัสผ่าน",
            show="●"
        )
        self.password_entry.pack(pady=(0, 15), padx=40, fill="x")
        
        # ปุ่มล็อกอิน
        self.login_button = ctk.CTkButton(
            login_frame,
            text="เข้าสู่ระบบ",
            font=("Sarabun", 16, "bold"),
            width=220,
            height=54,
            corner_radius=27,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            command=self.login
        )
        self.login_button.pack(pady=(0, 15))
        
        # ข้อมูลเริ่มต้น
        info_frame = ctk.CTkFrame(login_frame, fg_color=COLORS["light"], corner_radius=10)
        info_frame.pack(pady=(10, 30), padx=40, fill="x")
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="ผู้ใช้เริ่มต้น\nชื่อผู้ใช้: admin | รหัสผ่าน: admin",
            font=FONTS["small"],
            text_color=COLORS["text_light"],
            justify="center"
        )
        info_label.pack(pady=15)
        
        # เวอร์ชัน
        version_label = ctk.CTkLabel(
            main_frame,
            text=f"เวอร์ชัน {APP_VERSION}",
            font=FONTS["small"],
            text_color=COLORS["text_light"]
        )
        version_label.pack(pady=(10, 0))
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        
        # Focus ที่ username
        self.username_entry.focus()
        
    def login(self):
        """ตรวจสอบการล็อกอิน"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
            return
            
        # ตรวจสอบกับฐานข้อมูล
        if not self.db.connect():
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
            return
            
        user_id = self.db.verify_password(username, password)
        
        if user_id:
            # ดึงข้อมูลผู้ใช้
            self.user_info = self.db.get_user_info(user_id)
            
            if self.user_info:
                # บันทึกประวัติการเข้าใช้งาน
                self.db.execute(
                    "INSERT INTO login_history (user_id) VALUES (?)",
                    (user_id,)
                )
                
                self.db.disconnect()
                self.user_id = user_id
                
                # ปิดหน้า login และเปิดหน้าหลัก
                self.window.destroy()
            else:
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบข้อมูลผู้ใช้")
                self.db.disconnect()
        else:
            messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", MESSAGES["login_failed"])
            self.password_entry.delete(0, 'end')
            self.password_entry.focus()
            self.db.disconnect()
            
    def run(self):
        """เริ่มโปรแกรม"""
        # สร้างฐานข้อมูลถ้ายังไม่มี
        self.db.connect()
        self.db.initialize_database()
        self.db.disconnect()
        
        # โหลดคอนฟิกจากฐานข้อมูล
        from config import load_config_from_db
        load_config_from_db()
        
        self.window.mainloop()
        
        return self.user_id, self.user_info


if __name__ == "__main__":
    app = LoginWindow()
    user_id, user_info = app.run()
    
    if user_id:
        print(f"Login successful! User: {user_info['full_name']}")
    else:
        print("Login cancelled")
