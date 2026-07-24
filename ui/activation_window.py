# -*- coding: utf-8 -*-
"""
Activation Window - หน้าต่างสำหรับ Activate โปรแกรม
"""

import customtkinter as ctk
from tkinter import messagebox
from utils.license_system import HardwareID, LicenseManager
from config import COLORS, FONTS, get_responsive_dialog_geometry


class ActivationWindow(ctk.CTkToplevel):
    """หน้าต่าง Activation"""
    
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        
        self.on_success = on_success
        self.hwid = HardwareID.generate_hwid()
        
        self.title("🔐 Activate โปรแกรม POS")
        self.geometry(get_responsive_dialog_geometry(parent, 700, 620))
        self.resizable(True, True)
        
        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()
        
        self.create_widgets()
    
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["primary"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🔐 Activate โปรแกรม",
            font=("Sarabun", 24, "bold"),
            text_color="white"
        ).pack(pady=15)
        
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
        info_frame = ctk.CTkFrame(content, fg_color="#eef6fc", corner_radius=10)
        info_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ หมายเหตุ: License Key ผูกกับเครื่องนี้เท่านั้น\n📞 ช่องทางติดต่อรับ License Key / แจ้งปัญหา (เบอร์ / Line): 0848400908",
            font=("Sarabun", 13, "bold"),
            text_color=COLORS["primary"],
            wraplength=600,
            justify="center"
        ).pack(padx=15, pady=12)
        
        self.bind_context_menu(self.hwid_entry)
        self.bind_context_menu(self.license_entry)
        
    def bind_context_menu(self, widget):
        """ผูกเมนูคลิกขวา ตัด/คัดลอก/วาง สำหรับ Entry หรือ Textbox"""
        import tkinter as tk
        inner_widget = widget
        if hasattr(widget, "_entry"):
            inner_widget = widget._entry
        elif hasattr(widget, "_textbox"):
            inner_widget = widget._textbox
            
        menu = tk.Menu(inner_widget, tearoff=0)
        menu.add_command(label="ตัด (Cut)", command=lambda: inner_widget.event_generate("<<Cut>>"))
        menu.add_command(label="คัดลอก (Copy)", command=lambda: inner_widget.event_generate("<<Copy>>"))
        menu.add_command(label="วาง (Paste)", command=lambda: inner_widget.event_generate("<<Paste>>"))
        
        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
                
        inner_widget.bind("<Button-3>", show_menu)
    
    def copy_hwid(self):
        """Copy HWID ไปยัง Clipboard"""
        self.clipboard_clear()
        self.clipboard_append(self.hwid)
        messagebox.showinfo("สำเร็จ", "Copy HWID แล้ว!\n\nส่ง HWID นี้ให้ผู้ขายเพื่อรับ License Key", parent=self)
    
    def activate(self):
        """Activate โปรแกรม"""
        license_key = self.license_entry.get("1.0", "end").strip()
        
        if not license_key:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาใส่ License Key", parent=self)
            return
        
        # ตรวจสอบ License
        is_valid, message, license_data = LicenseManager.validate_license_key(license_key, self.hwid)
        
        if not is_valid:
            messagebox.showerror("Activation ล้มเหลว", f"License Key ไม่ถูกต้อง!\n\n{message}", parent=self)
            return
        
        # บันทึก License
        if LicenseManager.save_license(license_key):
            try:
                self.grab_release()
            except Exception:
                pass
                
            messagebox.showinfo(
                "Activation สำเร็จ! 🎉",
                f"{message}\n\nหมดอายุ: {license_data['expire_date']}\n\nกำลังเข้าสู่ระบบ...",
                parent=self
            )
            
            if self.on_success:
                self.on_success()
            
            self.destroy()
            try:
                self.master.update()
            except Exception:
                pass
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถบันทึก License ได้", parent=self)
    
    def cancel(self):
        """ยกเลิก"""
        try:
            self.grab_release()
        except Exception:
            pass
        result = messagebox.askyesno(
            "ยืนยัน",
            "ยกเลิกการ Activate?\n\n(โปรแกรมจะปิดตัวลง)",
            parent=self
        )
        if result:
            self.destroy()
            self.master.quit()
        else:
            try:
                self.grab_set()
            except Exception:
                pass


# ทดสอบ
if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    
    def on_success():
        print("Activation สำเร็จ!")
    
    window = ActivationWindow(root, on_success)
    root.mainloop()
