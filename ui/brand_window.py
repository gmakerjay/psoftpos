# -*- coding: utf-8 -*-
"""
หน้าจัดการแบรนด์สินค้า
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *

class BrandManagementFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการแบรนด์สินค้า"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        
        self.create_widgets()
        self.load_brands()

    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header_frame,
            text="🏷️ จัดการแบรนด์สินค้า",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        ).pack(side="left")
        
        # ปุ่มแจ้งเตือน/เพิ่ม
        add_btn = ctk.CTkButton(
            header_frame,
            text="➕ เพิ่มแบรนด์",
            font=FONTS["button"],
            fg_color=COLORS["success"],
            command=self.show_add_brand_dialog
        )
        add_btn.pack(side="right")
        
        # รายการแบรนด์
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="white",
            corner_radius=10
        )
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_brands(self):
        """โหลดรายการแบรนด์"""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        self.db.connect()
        brands = self.db.fetch_all("SELECT * FROM brands ORDER BY brand_name")
        self.db.disconnect()
        
        if not brands:
            ctk.CTkLabel(self.list_frame, text="ยังไม่มีข้อมูลแบรนด์", font=FONTS["body"]).pack(pady=20)
            return
            
        for brand in brands:
            row = ctk.CTkFrame(self.list_frame, fg_color=COLORS["light"], corner_radius=5)
            row.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(row, text=brand['brand_name'], font=FONTS["body"], width=200, anchor="w").pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(row, text=brand['description'] or "-", font=FONTS["small"], text_color=COLORS["text_light"]).pack(side="left", padx=15, fill="x", expand=True)
            
            # ปุ่มแก้ไข/ลบ
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)
            
            ctk.CTkButton(
                btn_frame, text="แก้ไข", width=60, height=30,
                fg_color=COLORS["warning"], command=lambda b=brand: self.show_edit_brand_dialog(b)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                btn_frame, text="ลบ", width=60, height=30,
                fg_color=COLORS["danger"], command=lambda b_id=brand['brand_id']: self.delete_brand(b_id)
            ).pack(side="left", padx=2)

    def show_add_brand_dialog(self):
        self.show_brand_dialog("เพิ่มแบรนด์ใหม่")

    def show_edit_brand_dialog(self, brand):
        self.show_brand_dialog("แก้ไขแบรนด์", brand)

    def show_brand_dialog(self, title, brand=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=title, font=FONTS["heading"]).pack(pady=20)
        
        # ชื่อแบรนด์
        ctk.CTkLabel(dialog, text="ชื่อแบรนด์:", font=FONTS["body"]).pack(padx=20, anchor="w")
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(padx=20, pady=(5, 15))
        if brand: name_entry.insert(0, brand['brand_name'])
        
        # คำอธิบาย
        ctk.CTkLabel(dialog, text="รายละเอียด:", font=FONTS["body"]).pack(padx=20, anchor="w")
        desc_entry = ctk.CTkEntry(dialog, width=300)
        desc_entry.pack(padx=20, pady=(5, 15))
        if brand: desc_entry.insert(0, brand['description'] or "")
        
        def save():
            name = name_entry.get().strip()
            desc = desc_entry.get().strip()
            if not name:
                messagebox.showerror("ผิดพลาด", "กรุณากรอกชื่อแบรนด์")
                return
                
            self.db.connect()
            if brand:
                success = self.db.execute(
                    "UPDATE brands SET brand_name = ?, description = ? WHERE brand_id = ?",
                    (name, desc, brand['brand_id'])
                )
            else:
                success = self.db.execute(
                    "INSERT INTO brands (brand_name, description) VALUES (?, ?)",
                    (name, desc)
                )
            self.db.disconnect()
            
            if success:
                messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลเรียบร้อย")
                dialog.destroy()
                self.load_brands()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกข้อมูลได้")
                
        ctk.CTkButton(dialog, text="บันทึก", fg_color=COLORS["primary"], command=save).pack(pady=20)

    def delete_brand(self, brand_id):
        if messagebox.askyesno("ยืนยัน", "คุณต้องการลบแบรนด์นี้ใช่หรือไม่?"):
            self.db.connect()
            success = self.db.execute("DELETE FROM brands WHERE brand_id = ?", (brand_id,))
            self.db.disconnect()
            if success:
                self.load_brands()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบข้อมูลได้")
