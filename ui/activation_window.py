# -*- coding: utf-8 -*-
"""
Activation Window - หน้าต่างสำหรับ Activate โปรแกรม
"""

import customtkinter as ctk
from tkinter import messagebox
from utils.license_system import HardwareID, LicenseManager
from config import COLORS, FONTS


class ActivationWindow(ctk.CTkToplevel):
    """หน้าต่าง Activation"""
    
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        
        self.on_success = on_success
        self.hwid = HardwareID.generate_hwid()
        
        self.title("🔐 Activate โปรแกรม POS")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"+{x}+{y}")
        
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🔐 Activate โปรแกรม",
            font=("Sarabun", 32, "bold"),
            text_color="white"
        ).pack(pady=30)
        
        # Content
        content = ctk.CTkFrame(self, fg_color="white")
        content.pack(fill="both", expand=True, padx=30, pady=30)
        
        # HWID Display
        hwid_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        hwid_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            hwid_frame,
            text="🖥️ Hardware ID ของคุณ:",
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["primary"]
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            hwid_frame,
            text="ส่ง Hardware ID นี้ให้ผู้ขายเพื่อรับ License Key",
            font=("Sarabun", 14),
            text_color=COLORS["text_light"]
        ).pack(pady=(0, 10))
        
        # HWID Entry (Read-only)
        self.hwid_entry = ctk.CTkEntry(
            hwid_frame,
            font=("Courier New", 16, "bold"),
            height=50,
            justify="center",
            fg_color="white",
            text_color=COLORS["danger"]
        )
        self.hwid_entry.pack(fill="x", padx=20, pady=(0, 10))
        self.hwid_entry.insert(0, self.hwid)
        self.hwid_entry.configure(state="readonly")
        
        # Copy Button
        copy_btn = ctk.CTkButton(
            hwid_frame,
            text="📋 Copy HWID",
            font=("Sarabun", 16),
            height=40,
            fg_color=COLORS["info"],
            command=self.copy_hwid
        )
        copy_btn.pack(pady=(0, 20))
        
        # License Key Input
        license_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        license_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            license_frame,
            text="🔑 ใส่ License Key:",
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["primary"]
        ).pack(pady=(20, 10))
        
        self.license_entry = ctk.CTkTextbox(
            license_frame,
            font=("Courier New", 12),
            height=120,
            fg_color="white"
        )
        self.license_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        activate_btn = ctk.CTkButton(
            btn_frame,
            text="✅ Activate โปรแกรม",
            font=("Sarabun", 18, "bold"),
            height=50,
            fg_color=COLORS["success"],
            command=self.activate
        )
        activate_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="❌ ยกเลิก",
            font=("Sarabun", 18),
            height=50,
            fg_color=COLORS["danger"],
            command=self.cancel
        )
        cancel_btn.pack(side="left", padx=(10, 0))
        
        # Info
        info_frame = ctk.CTkFrame(content, fg_color="#fff3cd", corner_radius=10)
        info_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ หมายเหตุ: License Key ผูกกับเครื่องนี้เท่านั้น ไม่สามารถใช้กับเครื่องอื่นได้",
            font=("Sarabun", 12),
            text_color="#856404",
            wraplength=600
        ).pack(padx=15, pady=15)
    
    def copy_hwid(self):
        """Copy HWID ไปยัง Clipboard"""
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        messagebox.showinfo("สำเร็จ", "Copy HWID แล้ว!\n\nส่ง HWID นี้ให้ผู้ขายเพื่อรับ License Key")
    
    def activate(self):
        """Activate โปรแกรม"""
        license_key = self.license_entry.get("1.0", "end").strip()
        
        if not license_key:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาใส่ License Key")
            return
        
        # ตรวจสอบ License
        is_valid, message, license_data = LicenseManager.validate_license_key(license_key, self.hwid)
        
        if not is_valid:
            messagebox.showerror("Activation ล้มเหลว", f"License Key ไม่ถูกต้อง!\n\n{message}")
            return
        
        # บันทึก License
        if LicenseManager.save_license(license_key):
            messagebox.showinfo(
                "Activation สำเร็จ! 🎉",
                f"{message}\n\nหมดอายุ: {license_data['expire_date']}\n\nกำลังเข้าสู่ระบบ..."
            )
            
            if self.on_success:
                self.on_success()
            
            self.destroy()
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถบันทึก License ได้")
    
    def cancel(self):
        """ยกเลิก"""
        result = messagebox.askyesno(
            "ยืนยัน",
            "ยกเลิกการ Activate?\n\n(โปรแกรมจะปิดตัวลง)"
        )
        if result:
            self.destroy()
            self.master.quit()


# ทดสอบ
if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    
    def on_success():
        print("Activation สำเร็จ!")
    
    window = ActivationWindow(root, on_success)
    root.mainloop()
