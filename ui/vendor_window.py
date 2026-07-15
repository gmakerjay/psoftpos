# -*- coding: utf-8 -*-
"""
หน้าจัดการผู้จัดจำหน่าย (Vendors)
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *

class VendorManagementFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการผู้จัดจำหน่าย"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        
        self.create_widgets()
        self.load_vendors()

    def create_widgets(self):
        """สร้าง UI"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header_frame,
            text="🏢 จัดการผู้จัดจำหน่าย",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        ).pack(side="left")
        
        add_btn = ctk.CTkButton(
            header_frame,
            text="➕ เพิ่มผู้จัดจำหน่าย",
            font=FONTS["button"],
            fg_color=COLORS["success"],
            command=self.show_add_vendor_dialog
        )
        add_btn.pack(side="right")
        
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="white",
            corner_radius=10
        )
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_vendors(self):
        """โหลดรายการผู้จัดจำหน่าย"""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        self.db.connect()
        vendors = self.db.fetch_all("SELECT * FROM vendors ORDER BY vendor_name")
        self.db.disconnect()
        
        if not vendors:
            ctk.CTkLabel(self.list_frame, text="ยังไม่มีข้อมูลผู้จัดจำหน่าย", font=FONTS["body"]).pack(pady=20)
            return
            
        for vendor in vendors:
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["light"], corner_radius=5)
            row.pack(fill="x", padx=5, pady=5)
            
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=10, fill="x", expand=True)
            
            ctk.CTkLabel(info_frame, text=vendor['vendor_name'], font=FONTS["heading"], anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"📞 {vendor['phone'] or '-'} | 👤 {vendor['contact_name'] or '-'}", font=FONTS["small"], text_color=COLORS["text_light"], anchor="w").pack(fill="x")
            
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(btn_frame, text="แก้ไข", width=60, height=30, fg_color=COLORS["warning"], command=lambda v=vendor: self.show_edit_vendor_dialog(v)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="ลบ", width=60, height=30, fg_color=COLORS["danger"], command=lambda v_id=vendor['vendor_id']: self.delete_vendor(v_id)).pack(side="left", padx=2)

    def show_add_vendor_dialog(self):
        self.show_vendor_dialog("เพิ่มผู้จัดจำหน่าย")

    def show_edit_vendor_dialog(self, vendor):
        self.show_vendor_dialog("แก้ไขผู้จัดจำหน่าย", vendor)

    def show_vendor_dialog(self, title, vendor=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=title, font=FONTS["heading"]).pack(pady=20)
        
        fields = [
            ("vendor_name", "ชื่อบริษัท/ร้านค้า:"),
            ("contact_name", "ผู้ติดต่อ:"),
            ("phone", "เบอร์โทรศัพท์:"),
            ("email", "อีเมล:"),
            ("address", "ที่อยู่:"),
            ("tax_id", "เลขประจำตัวผู้เสียภาษี:"),
        ]
        
        entries = {}
        for key, label in fields:
            ctk.CTkLabel(dialog, text=label, font=FONTS["body"]).pack(padx=20, anchor="w")
            entry = ctk.CTkEntry(dialog, width=400)
            entry.pack(padx=20, pady=(2, 10))
            if vendor: entry.insert(0, vendor[key] or "")
            entries[key] = entry
            
        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            if not data["vendor_name"]:
                messagebox.showerror("ผิดพลาด", "กรุณากรอกชื่อผู้จัดจำหน่าย")
                return
                
            self.db.connect()
            if vendor:
                query = "UPDATE vendors SET " + ", ".join([f"{k} = ?" for k in data.keys()]) + " WHERE vendor_id = ?"
                params = list(data.values()) + [vendor['vendor_id']]
                success = self.db.execute(query, params)
            else:
                query = "INSERT INTO vendors (" + ", ".join(data.keys()) + ") VALUES (" + ", ".join(["?" for _ in data]) + ")"
                success = self.db.execute(query, list(data.values()))
            self.db.disconnect()
            
            if success:
                messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลเรียบร้อย")
                dialog.destroy()
                self.load_vendors()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกข้อมูลได้")
                
        ctk.CTkButton(dialog, text="บันทึก", fg_color=COLORS["primary"], height=40, command=save).pack(pady=30)

    def delete_vendor(self, vendor_id):
        if messagebox.askyesno("ยืนยัน", "หากลบผู้จัดจำหน่าย สินค้าที่เชื่อมโยงจะยังอยู่แต่ข้อมูลผู้จัดจะหายไป คุณต้องการลบใช่หรือไม่?"):
            self.db.connect()
            success = self.db.execute("DELETE FROM vendors WHERE vendor_id = ?", (vendor_id,))
            self.db.disconnect()
            if success:
                self.load_vendors()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบข้อมูลได้")
