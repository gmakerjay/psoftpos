# -*- coding: utf-8 -*-
"""
License Manager - โปรแกรมจัดการ License (สำหรับนักพัฒนา)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import customtkinter as ctk
from tkinter import messagebox, filedialog
from utils.license_system import LicenseManager
import json
from datetime import datetime


class LicenseManagerApp(ctk.CTk):
    """โปรแกรมจัดการ License สำหรับนักพัฒนา"""
    
    # รหัสผ่านนักพัฒนา (ควรเปลี่ยนเป็นรหัสที่ปลอดภัยกว่านี้)
    DEVELOPER_PASSWORD = "DEV2024@SECURE"
    
    def __init__(self):
        super().__init__()
        
        self.title("🔧 License Manager - Developer Tools")
        self.geometry("1000x700")
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        self.is_authenticated = False
        self.create_login_screen()
    
    def create_login_screen(self):
        """หน้า Login สำหรับนักพัฒนา"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
        
        # Login Frame
        login_frame = ctk.CTkFrame(self, fg_color="#1A1A1A")
        login_frame.pack(fill="both", expand=True)
        
        # Center Content
        center = ctk.CTkFrame(login_frame, fg_color="#2D2D2D", corner_radius=20)
        center.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(
            center,
            text="🔧 Developer Access",
            font=("Sarabun", 32, "bold"),
            text_color="#4CAF50"
        ).pack(pady=(40, 10))
        
        ctk.CTkLabel(
            center,
            text="License Manager - For Developers Only",
            font=("Sarabun", 14),
            text_color="#9E9E9E"
        ).pack(pady=(0, 30))
        
        self.password_entry = ctk.CTkEntry(
            center,
            placeholder_text="Enter Developer Password",
            font=("Courier New", 16),
            width=350,
            height=50,
            show="●"
        )
        self.password_entry.pack(padx=50, pady=10)
        self.password_entry.bind("<Return>", lambda e: self.verify_password())
        
        ctk.CTkButton(
            center,
            text="🔓 Unlock",
            font=("Sarabun", 18, "bold"),
            width=350,
            height=50,
            fg_color="#4CAF50",
            command=self.verify_password
        ).pack(padx=50, pady=(10, 40))
        
        self.password_entry.focus()
    
    def verify_password(self):
        """ตรวจสอบรหัสผ่าน"""
        password = self.password_entry.get()
        
        if password == self.DEVELOPER_PASSWORD:
            self.is_authenticated = True
            self.create_main_screen()
        else:
            messagebox.showerror("Access Denied", "รหัสผ่านไม่ถูกต้อง!")
            self.password_entry.delete(0, "end")
    
    def create_main_screen(self):
        """หน้าจัดการ License"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
        
        # === Header ===
        header = ctk.CTkFrame(self, fg_color="#2E7D32", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🔧 License Manager",
            font=("Sarabun", 28, "bold"),
            text_color="white"
        ).pack(side="left", padx=30)
        
        ctk.CTkButton(
            header,
            text="🔒 Logout",
            font=("Sarabun", 14),
            width=100,
            fg_color="#D32F2F",
            command=self.logout
        ).pack(side="right", padx=30)
        
        # === Main Content ===
        main_frame = ctk.CTkFrame(self, fg_color="#1A1A1A")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tabview
        tabview = ctk.CTkTabview(main_frame, fg_color="#2D2D2D")
        tabview.pack(fill="both", expand=True)
        
        # Tabs
        tab1 = tabview.add("📋 View License")
        tab2 = tabview.add("🗑️ Delete License")
        tab3 = tabview.add("✏️ Edit License")
        tab4 = tabview.add("📊 Validate License")
        
        # === Tab 1: View License ===
        self.create_view_tab(tab1)
        
        # === Tab 2: Delete License ===
        self.create_delete_tab(tab2)
        
        # === Tab 3: Edit License ===
        self.create_edit_tab(tab3)
        
        # === Tab 4: Validate License ===
        self.create_validate_tab(tab4)
    
    def create_view_tab(self, parent):
        """Tab สำหรับดู License"""
        ctk.CTkLabel(
            parent,
            text="📋 ดูข้อมูล License ปัจจุบัน",
            font=("Sarabun", 22, "bold")
        ).pack(pady=20)
        
        ctk.CTkButton(
            parent,
            text="🔍 โหลดข้อมูล License",
            font=("Sarabun", 16),
            height=45,
            fg_color="#1976D2",
            command=self.load_license_info
        ).pack(pady=10)
        
        self.view_text = ctk.CTkTextbox(
            parent,
            font=("Courier New", 11),
            fg_color="#2D2D2D"
        )
        self.view_text.pack(fill="both", expand=True, padx=20, pady=10)
    
    def create_delete_tab(self, parent):
        """Tab สำหรับลบ License"""
        ctk.CTkLabel(
            parent,
            text="🗑️ ลบ License",
            font=("Sarabun", 22, "bold"),
            text_color="#F44336"
        ).pack(pady=20)
        
        ctk.CTkLabel(
            parent,
            text="⚠️ คำเตือน: การลบ License จะทำให้โปรแกรมไม่สามารถใช้งานได้",
            font=("Sarabun", 14),
            text_color="#FFC107"
        ).pack(pady=10)
        
        ctk.CTkButton(
            parent,
            text="🗑️ ลบ License File",
            font=("Sarabun", 18, "bold"),
            height=60,
            fg_color="#D32F2F",
            command=self.delete_license
        ).pack(pady=20)
        
        self.delete_status = ctk.CTkLabel(
            parent,
            text="",
            font=("Sarabun", 16)
        )
        self.delete_status.pack(pady=10)
    
    def create_edit_tab(self, parent):
        """Tab สำหรับแก้ไข License"""
        ctk.CTkLabel(
            parent,
            text="✏️ แก้ไข License (Advanced)",
            font=("Sarabun", 22, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            parent,
            text="วาง License Key ใหม่ที่ต้องการแทนที่:",
            font=("Sarabun", 14)
        ).pack(pady=10)
        
        self.edit_license_entry = ctk.CTkTextbox(
            parent,
            font=("Courier New", 11),
            height=100,
            fg_color="#2D2D2D"
        )
        self.edit_license_entry.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            parent,
            text="💾 บันทึก License ใหม่",
            font=("Sarabun", 16),
            height=50,
            fg_color="#FB8C00",
            command=self.save_new_license
        ).pack(pady=10)
        
        self.edit_status = ctk.CTkLabel(
            parent,
            text="",
            font=("Sarabun", 14)
        )
        self.edit_status.pack(pady=10)
    
    def create_validate_tab(self, parent):
        """Tab สำหรับตรวจสอบ License"""
        ctk.CTkLabel(
            parent,
            text="📊 ตรวจสอบความถูกต้องของ License",
            font=("Sarabun", 22, "bold")
        ).pack(pady=20)
        
        # HWID Input
        hwid_frame = ctk.CTkFrame(parent, fg_color="#2D2D2D", corner_radius=10)
        hwid_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            hwid_frame,
            text="Hardware ID:",
            font=("Sarabun", 14)
        ).pack(pady=(10, 5))
        
        self.validate_hwid_entry = ctk.CTkEntry(
            hwid_frame,
            font=("Courier New", 14),
            height=45,
            placeholder_text="XXXX-XXXX-XXXX-XXXX"
        )
        self.validate_hwid_entry.pack(fill="x", padx=20, pady=5)
        
        # License Key Input
        ctk.CTkLabel(
            hwid_frame,
            text="License Key:",
            font=("Sarabun", 14)
        ).pack(pady=(10, 5))
        
        self.validate_license_entry = ctk.CTkTextbox(
            hwid_frame,
            font=("Courier New", 11),
            height=100
        )
        self.validate_license_entry.pack(fill="x", padx=20, pady=(5, 15))
        
        ctk.CTkButton(
            parent,
            text="✔️ ตรวจสอบ",
            font=("Sarabun", 16),
            height=50,
            fg_color="#43A047",
            command=self.validate_license
        ).pack(pady=10)
        
        self.validate_result = ctk.CTkTextbox(
            parent,
            font=("Courier New", 11),
            height=200,
            fg_color="#2D2D2D"
        )
        self.validate_result.pack(fill="both", expand=True, padx=20, pady=10)
    
    def load_license_info(self):
        """โหลดข้อมูล License"""
        license_key = LicenseManager.load_license()
        
        if not license_key:
            self.view_text.delete("1.0", "end")
            self.view_text.insert("1.0", "❌ ไม่พบ License File\n\nโปรแกรมยังไม่ได้ Activate")
            return
        
        # ตรวจสอบ License
        is_valid, message, license_data = LicenseManager.check_activation()
        
        result = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                        LICENSE INFORMATION                            ║
╚═══════════════════════════════════════════════════════════════════════╝

Status: {"✅ VALID" if is_valid else "❌ INVALID"}
Message: {message}

"""
        
        if license_data:
            result += f"""📄 License Data:
   - HWID: {license_data.get('hwid', 'N/A')}
   - Expire Date: {license_data.get('expire_date', 'N/A')}
   - Issued Date: {license_data.get('issued_date', 'N/A')}

✨ Features:
"""
            for key, value in license_data.get('features', {}).items():
                status = "✅ Enabled" if value else "❌ Disabled"
                result += f"   {status} {key}\n"
        
        result += f"\n\n🔑 Raw License Key:\n{license_key}\n"
        
        self.view_text.delete("1.0", "end")
        self.view_text.insert("1.0", result)
    
    def delete_license(self):
        """ลบ License"""
        result = messagebox.askyesno(
            "ยืนยันการลบ",
            "คุณแน่ใจหรือไม่ว่าต้องการลบ License?\n\n"
            "โปรแกรมจะไม่สามารถใช้งานได้จนกว่าจะ Activate ใหม่"
        )
        
        if result:
            if LicenseManager.delete_license():
                self.delete_status.configure(text="✅ ลบ License สำเร็จ", text_color="#4CAF50")
                messagebox.showinfo("สำเร็จ", "ลบ License สำเร็จ!")
            else:
                self.delete_status.configure(text="❌ ไม่พบ License", text_color="#F44336")
    
    def save_new_license(self):
        """บันทึก License ใหม่"""
        license_key = self.edit_license_entry.get("1.0", "end").strip()
        
        if not license_key:
            self.edit_status.configure(text="❌ กรุณาใส่ License Key", text_color="#F44336")
            return
        
        if LicenseManager.save_license(license_key):
            self.edit_status.configure(text="✅ บันทึก License สำเร็จ", text_color="#4CAF50")
            messagebox.showinfo("สำเร็จ", "บันทึก License ใหม่สำเร็จ!")
        else:
            self.edit_status.configure(text="❌ ไม่สามารถบันทึกได้", text_color="#F44336")
    
    def validate_license(self):
        """ตรวจสอบ License"""
        hwid = self.validate_hwid_entry.get().strip()
        license_key = self.validate_license_entry.get("1.0", "end").strip()
        
        if not hwid or not license_key:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาใส่ทั้ง HWID และ License Key")
            return
        
        is_valid, message, license_data = LicenseManager.validate_license_key(license_key, hwid)
        
        result = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║                        VALIDATION RESULT                              ║
╚═══════════════════════════════════════════════════════════════════════╝

Status: {"✅ VALID" if is_valid else "❌ INVALID"}
Message: {message}

🖥️ Hardware ID: {hwid}

"""
        
        if license_data:
            result += f"""📄 License Data:
   - HWID Match: {"✅ Yes" if license_data['hwid'] == hwid else "❌ No"}
   - Expire Date: {license_data.get('expire_date', 'N/A')}
   - Issued Date: {license_data.get('issued_date', 'N/A')}
   
✨ Features:
"""
            for key, value in license_data.get('features', {}).items():
                status = "✅" if value else "❌"
                result += f"   {status} {key}\n"
        
        self.validate_result.delete("1.0", "end")
        self.validate_result.insert("1.0", result)
    
    def logout(self):
        """Logout"""
        result = messagebox.askyesno("ยืนยัน", "ออกจากระบบ?")
        if result:
            self.is_authenticated = False
            self.create_login_screen()


if __name__ == "__main__":
    app = LicenseManagerApp()
    app.mainloop()
