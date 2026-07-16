# -*- coding: utf-8 -*-
"""
หน้าตั้งค่า (Settings) - ครบทุกฟีเจอร์สำหรับร้านค้า One Stop Service
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinter.simpledialog import askstring
from database import DatabaseManager
from config import *
import shutil
import os
from pathlib import Path
from datetime import datetime


class SettingsFrame(ctk.CTkFrame):
    """Frame สำหรับตั้งค่าระบบ"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        
        self.create_widgets()
        self.load_settings()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        title = ctk.CTkLabel(
            self,
            text="⚙️ ตั้งค่าระบบ",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(padx=20, pady=20, anchor="w")
        
        # แท็บ
        self.tab_view = ctk.CTkTabview(self, corner_radius=10)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # แท็บต่างๆ
        self.tab_view.add("ข้อมูลร้าน")
        self.tab_view.add("ภาษีและราคา")
        self.tab_view.add("ใบเสร็จ")
        self.tab_view.add("สำรองข้อมูล")
        self.tab_view.add("เครื่องพิมพ์")
        self.tab_view.add("ขั้นสูง")
        
        # สร้างเนื้อหาแต่ละแท็บ
        self.create_company_tab()
        self.create_tax_tab()
        self.create_receipt_tab()
        self.create_backup_tab()
        self.create_printer_tab()
        self.create_advanced_tab()
    
    def create_company_tab(self):
        """แท็บข้อมูลร้าน"""
        tab = self.tab_view.tab("ข้อมูลร้าน")
        
        # คำอธิบาย
        desc = ctk.CTkLabel(
            tab,
            text="ข้อมูลนี้จะแสดงในใบเสร็จและเอกสารต่างๆ",
            font=FONTS["body"],
            text_color=COLORS["text_light"]
        )
        desc.pack(padx=20, pady=(10, 20))
        
        # ฟอร์ม
        form_frame = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        fields = [
            ("ชื่อร้าน:", "name", COMPANY_INFO['name']),
            ("ที่อยู่:", "address", COMPANY_INFO['address']),
            ("โทรศัพท์:", "phone", COMPANY_INFO['phone']),
            ("เลขประจำตัวผู้เสียภาษี:", "tax_id", COMPANY_INFO['tax_id']),
            ("อีเมล:", "email", COMPANY_INFO['email']),
            ("เว็บไซต์:", "website", COMPANY_INFO['website']),
        ]
        
        self.company_entries = {}
        
        for label, key, default in fields:
            field_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            field_frame.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(
                field_frame,
                text=label,
                font=FONTS["body"],
                width=200,
                anchor="w"
            ).pack(side="left", padx=(0, 10))
            
            entry = ctk.CTkEntry(
                field_frame,
                font=FONTS["body"],
                height=40
            )
            entry.insert(0, default)
            entry.pack(side="left", fill="x", expand=True)
            
            self.company_entries[key] = entry
            
        # --- เพิ่มช่องเลือกรูป QR Code ---
        qr_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        qr_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            qr_frame,
            text="QR Code รับเงิน:",
            font=FONTS["body"],
            width=200,
            anchor="w"
        ).pack(side="left", padx=(0, 10))
        
        self.qr_path_entry = ctk.CTkEntry(
            qr_frame,
            font=FONTS["body"],
            height=40,
            placeholder_text="เลือกไฟล์รูปภาพ QR Code..."
        )
        self.qr_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        def browse_qr():
            path = filedialog.askopenfilename(
                title="เลือกรูป QR Code",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
            )
            if path:
                self.qr_path_entry.delete(0, 'end')
                self.qr_path_entry.insert(0, path)
        
        ctk.CTkButton(
            qr_frame,
            text="📁 เลือกรูป",
            font=FONTS["small"],
            width=100,
            height=40,
            fg_color=COLORS["info"],
            command=browse_qr
        ).pack(side="right")
        
        # โหลดค่าเก่า (ถ้ามี)
        self.db.connect()
        qr_setting = self.db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
        self.db.disconnect()
        if qr_setting:
            self.qr_path_entry.insert(0, qr_setting['setting_value'])

        # ปุ่มบันทึก
        save_btn = ctk.CTkButton(
            tab,
            text="💾 บันทึกข้อมูลร้าน",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color=COLORS["success"],
            command=self.save_company_info
        )
        save_btn.pack(padx=20, pady=(0, 20))
    
    def create_tax_tab(self):
        """แท็บภาษีและราคา"""
        tab = self.tab_view.tab("ภาษีและราคา")
        
        content = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ภาษี VAT
        vat_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        vat_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            vat_frame,
            text="📊 อัตราภาษี VAT (%)",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        vat_row = ctk.CTkFrame(vat_frame, fg_color="transparent")
        vat_row.pack(fill="x", padx=20, pady=(0, 20))
        
        self.vat_entry = ctk.CTkEntry(
            vat_row,
            font=("Sarabun", 18),
            height=50,
            width=150,
            justify="center"
        )
        self.vat_entry.insert(0, str(round(TAX_RATE * 100, 2)))
        self.vat_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            vat_row,
            text="%",
            font=("Sarabun", 18, "bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            vat_frame,
            text="หมายเหตุ: เปลี่ยนแปลงจะมีผลกับรายการขายใหม่เท่านั้น",
            font=FONTS["small"],
            text_color=COLORS["text_light"]
        ).pack(padx=20, pady=(0, 15))
        
        # ประเภทราคา
        price_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        price_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            price_frame,
            text="🏷️ ประเภทราคา",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        price_types = [
            ("ราคาปลีก", "retail_price"),
            ("ราคาส่ง", "wholesale_price"),
            ("ราคาพิเศษ 1", "special_price_1"),
            ("ราคาพิเศษ 2", "special_price_2"),
        ]
        
        for thai_name, key in price_types:
            row = ctk.CTkFrame(price_frame, fg_color="white", corner_radius=5)
            row.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(
                row,
                text=thai_name,
                font=FONTS["body"],
                width=150,
                anchor="w"
            ).pack(side="left", padx=15, pady=10)
            
            ctk.CTkLabel(
                row,
                text=f"สำหรับลูกค้า: {PRICE_TYPES.get(key.replace('_price', ''), key)}",
                font=FONTS["small"],
                text_color=COLORS["text_light"]
            ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            price_frame,
            text="",
            font=FONTS["small"]
        ).pack(pady=10)
        
        # ปุ่มบันทึก
        save_btn = ctk.CTkButton(
            content,
            text="💾 บันทึกการตั้งค่า",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color=COLORS["success"],
            command=self.save_tax_settings
        )
        save_btn.pack(padx=20, pady=(0, 20))
    
    def create_receipt_tab(self):
        """แท็บใบเสร็จ"""
        tab = self.tab_view.tab("ใบเสร็จ")
        
        content = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ข้อความท้ายใบเสร็จ
        message_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        message_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            message_frame,
            text="📝 ข้อความท้ายใบเสร็จ",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        self.receipt_message = ctk.CTkTextbox(
            message_frame,
            font=FONTS["body"],
            height=100
        )
        self.receipt_message.insert("1.0", "ขอบคุณที่อุดหนุน\nยินดีให้บริการ")
        self.receipt_message.pack(fill="x", padx=20, pady=(0, 20))
        
        # ตัวเลือก
        options_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        options_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            options_frame,
            text="⚙️ ตัวเลือกการพิมพ์",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        self.show_barcode_var = ctk.BooleanVar(value=True)
        self.show_cashier_var = ctk.BooleanVar(value=True)
        self.auto_print_var = ctk.BooleanVar(value=False)
        
        options = [
            ("แสดงบาร์โค้ดในใบเสร็จ", self.show_barcode_var),
            ("แสดงชื่อพนักงานขาย", self.show_cashier_var),
            ("พิมพ์อัตโนมัติหลังขาย", self.auto_print_var),
        ]
        
        for text, var in options:
            cb = ctk.CTkCheckBox(
                options_frame,
                text=text,
                variable=var,
                font=FONTS["body"]
            )
            cb.pack(padx=30, pady=5, anchor="w")
        
        ctk.CTkLabel(
            options_frame,
            text="",
            font=FONTS["small"]
        ).pack(pady=10)
        
        # ปุ่มบันทึก
        save_btn = ctk.CTkButton(
            content,
            text="💾 บันทึกการตั้งค่า",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color=COLORS["success"],
            command=self.save_receipt_settings
        )
        save_btn.pack(padx=20, pady=(0, 20))
    
    def create_backup_tab(self):
        """แท็บสำรองข้อมูล"""
        tab = self.tab_view.tab("สำรองข้อมูล")
        
        content = ctk.CTkFrame(tab, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # คำอธิบาย
        desc_frame = ctk.CTkFrame(content, fg_color=COLORS["info"], corner_radius=10)
        desc_frame.pack(fill="x", padx=20, pady=20)
        
        from config import DATABASE_PATH
        desc_text = """
        💡 สำคัญ: สำรองข้อมูลเป็นประจำเพื่อความปลอดภัย
        
        ข้อมูลที่จะสำรอง:
        • ฐานข้อมูลทั้งหมด (database.db)
        • รูปภาพสินค้า (data/products/)
        • ใบเสร็จ (data/receipts/)
        • การตั้งค่าระบบ
        """
        
        ctk.CTkLabel(
            desc_frame,
            text=desc_text,
            font=FONTS["body"],
            text_color="white",
            justify="left"
        ).pack(padx=20, pady=20)
        
        # ข้อมูลฐานข้อมูล
        db_info_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        db_info_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # ขนาดฐานข้อมูล
        db_path = Path(DATABASE_PATH)
        if db_path.exists():
            db_size = db_path.stat().st_size / 1024 / 1024  # MB
            db_modified = datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
            
            info_text = f"""
            📊 ข้อมูลฐานข้อมูล
            
            ขนาด: {db_size:.2f} MB
            แก้ไขล่าสุด: {db_modified}
            ตำแหน่ง: {db_path.absolute()}
            """
        else:
            info_text = "ไม่พบไฟล์ฐานข้อมูล"
        
        ctk.CTkLabel(
            db_info_frame,
            text=info_text,
            font=FONTS["body"],
            justify="left"
        ).pack(padx=20, pady=15)
        
        # ปุ่ม
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        backup_btn = ctk.CTkButton(
            btn_frame,
            text="💾 สำรองข้อมูล",
            font=("Sarabun", 16, "bold"),
            height=60,
            fg_color=COLORS["success"],
            command=self.backup_database
        )
        backup_btn.pack(side="left", fill="x", expand=True, padx=5)
        
        restore_btn = ctk.CTkButton(
            btn_frame,
            text="♻️ กู้คืนข้อมูล",
            font=("Sarabun", 16, "bold"),
            height=60,
            fg_color=COLORS["warning"],
            command=self.restore_database
        )
        restore_btn.pack(side="left", fill="x", expand=True, padx=5)
    
    def create_printer_tab(self):
        """แท็บเครื่องพิมพ์"""
        tab = self.tab_view.tab("เครื่องพิมพ์")
        
        content = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ประเภทเครื่องพิมพ์
        printer_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        printer_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            printer_frame,
            text="🖨️ ประเภทเครื่องพิมพ์",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        self.printer_type_var = ctk.StringVar(value="pdf")
        
        printer_types = [
            ("PDF (บันทึกเป็นไฟล์)", "pdf"),
            ("Windows Printer (เครื่องพิมพ์ทั่วไป)", "windows"),
            ("Thermal Printer (เครื่องพิมพ์ใบเสร็จ)", "thermal"),
        ]
        
        for text, value in printer_types:
            rb = ctk.CTkRadioButton(
                printer_frame,
                text=text,
                variable=self.printer_type_var,
                value=value,
                font=FONTS["body"]
            )
            rb.pack(padx=30, pady=5, anchor="w")
        
        ctk.CTkLabel(
            printer_frame,
            text="",
            font=FONTS["small"]
        ).pack(pady=10)
        
        # เลือกเครื่องพิมพ์
        select_printer_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        select_printer_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            select_printer_frame,
            text="🖨️ เลือกเครื่องพิมพ์",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        printer_select_row = ctk.CTkFrame(select_printer_frame, fg_color="transparent")
        printer_select_row.pack(fill="x", padx=20, pady=(0, 20))
        
        self.printer_name_var = ctk.StringVar(value="")
        self.printer_combo = ctk.CTkComboBox(
            printer_select_row,
            values=["กำลังโหลด..."],
            variable=self.printer_name_var,
            width=300,
            font=FONTS["body"]
        )
        self.printer_combo.pack(side="left", padx=(0, 10))
        
        refresh_printers_btn = ctk.CTkButton(
            printer_select_row,
            text="🔄 รีเฟรช",
            font=FONTS["button"],
            width=100,
            fg_color=COLORS["info"],
            command=self.load_available_printers
        )
        refresh_printers_btn.pack(side="left")
        
        # ขนาดกระดาษ
        paper_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        paper_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            paper_frame,
            text="📄 ขนาดกระดาษ",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(20, 10))
        
        paper_row = ctk.CTkFrame(paper_frame, fg_color="transparent")
        paper_row.pack(fill="x", padx=20, pady=(0, 20))
        
        self.paper_size_var = ctk.StringVar(value="A4")
        paper_combo = ctk.CTkComboBox(
            paper_row,
            values=["80mm", "58mm", "A4", "A5", "100x150mm"],
            variable=self.paper_size_var,
            width=200,
            font=FONTS["body"]
        )
        paper_combo.pack(side="left")
        
        # โหลดเครื่องพิมพ์ตอน init
        self.load_available_printers()
        
        # ปุ่มทดสอบ
        test_btn = ctk.CTkButton(
            content,
            text="🧪 ทดสอบพิมพ์",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color=COLORS["info"],
            command=self.test_print
        )
        test_btn.pack(padx=20, pady=(0, 10))
        
        # ปุ่มบันทึก
        save_btn = ctk.CTkButton(
            content,
            text="💾 บันทึกการตั้งค่า",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color=COLORS["success"],
            command=self.save_printer_settings
        )
        save_btn.pack(padx=20, pady=(0, 20))
    
    def create_advanced_tab(self):
        """แท็บขั้นสูง"""
        tab = self.tab_view.tab("ขั้นสูง")
        
        content = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # คำเตือน
        warning_frame = ctk.CTkFrame(content, fg_color=COLORS["danger"], corner_radius=10)
        warning_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            warning_frame,
            text="⚠️ คำเตือน: การตั้งค่าในส่วนนี้สำหรับผู้ใช้ขั้นสูงเท่านั้น",
            font=("Sarabun", 14, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        # ล้างข้อมูล
        clear_frame = ctk.CTkFrame(content, fg_color=COLORS["light"], corner_radius=10)
        clear_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            clear_frame,
            text="🗑️ ล้างข้อมูล",
            font=FONTS["heading"],
            text_color=COLORS["danger"]
        ).pack(padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            clear_frame,
            text="ลบข้อมูลเก่าเพื่อเพิ่มประสิทธิภาพ (ระวัง: ไม่สามารถกู้คืนได้)",
            font=FONTS["body"],
            text_color=COLORS["text_light"]
        ).pack(padx=20, pady=(0, 10))
        
        clear_btn_frame = ctk.CTkFrame(clear_frame, fg_color="transparent")
        clear_btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            clear_btn_frame,
            text="ล้างประวัติการล็อกอิน",
            font=FONTS["button"],
            height=45,
            width=200,
            fg_color=COLORS["text_light"],
            command=self.clear_login_history
        ).pack(side="left", padx=5)
        
        # รีเซ็ตระบบ
        reset_frame = ctk.CTkFrame(content, fg_color="#ff6b6b", corner_radius=10)
        reset_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            reset_frame,
            text="🔄 รีเซ็ตระบบ",
            font=FONTS["heading"],
            text_color="white"
        ).pack(padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            reset_frame,
            text="ลบข้อมูลทั้งหมดและเริ่มต้นใหม่ (กรุณาสำรองข้อมูลก่อน!)",
            font=FONTS["body"],
            text_color="white"
        ).pack(padx=20, pady=(0, 10))
        
        reset_btn = ctk.CTkButton(
            reset_frame,
            text="⚠️ รีเซ็ตระบบทั้งหมด",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color="#d63031",
            hover_color="#b71c1c",
            command=self.reset_system
        )
        reset_btn.pack(padx=20, pady=(0, 20))
    
    def load_settings(self):
        """โหลดการตั้งค่า"""
        self.db.connect()
        settings = self.db.fetch_all("SELECT * FROM settings")
        self.db.disconnect()
        
        # แก้ไขจาก key/value เป็น setting_key/setting_value
        self.settings_dict = {s['setting_key']: s['setting_value'] for s in settings}

        # ป้อนข้อมูลกลับเข้า UI ฟิลด์ต่างๆ
        # แท็บข้อมูลร้าน
        for key, entry in self.company_entries.items():
            db_key = f"company_{key}"
            if db_key in self.settings_dict:
                entry.delete(0, 'end')
                entry.insert(0, self.settings_dict[db_key])

        # แท็บภาษีและราคา
        if 'tax_rate' in self.settings_dict:
            try:
                vat_val = float(self.settings_dict['tax_rate']) * 100
                self.vat_entry.delete(0, 'end')
                self.vat_entry.insert(0, f"{vat_val:.2f}".rstrip('0').rstrip('.'))
            except ValueError:
                pass

        # แท็บใบเสร็จ
        if 'receipt_message' in self.settings_dict:
            self.receipt_message.delete("1.0", "end")
            self.receipt_message.insert("1.0", self.settings_dict['receipt_message'])

        if 'receipt_show_barcode' in self.settings_dict:
            self.show_barcode_var.set(self.settings_dict['receipt_show_barcode'] == 'True')

        if 'receipt_show_cashier' in self.settings_dict:
            self.show_cashier_var.set(self.settings_dict['receipt_show_cashier'] == 'True')

        if 'receipt_auto_print' in self.settings_dict:
            self.auto_print_var.set(self.settings_dict['receipt_auto_print'] == 'True')

        # แท็บเครื่องพิมพ์
        if 'printer_type' in self.settings_dict:
            self.printer_type_var.set(self.settings_dict['printer_type'])

        if 'printer_name' in self.settings_dict:
            self.printer_name_var.set(self.settings_dict['printer_name'])

        if 'paper_size' in self.settings_dict:
            self.paper_size_var.set(self.settings_dict['paper_size'])
    
    def save_company_info(self):
        """บันทึกข้อมูลร้าน"""
        self.db.connect()
        
        for key, entry in self.company_entries.items():
            value = entry.get().strip()
            
            # อัพเดทหรือเพิ่ม - แก้ไขชื่อ column
            self.db.execute("""
                INSERT INTO settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
            """, (f"company_{key}", value, value))
        
        # บันทึก QR Path
        qr_path = self.qr_path_entry.get().strip()
        self.db.execute("""
            INSERT INTO settings (setting_key, setting_value)
            VALUES ('payment_qr_path', ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
        """, (qr_path, qr_path))
        
        self.db.disconnect()
        
        # รีโหลดคอนฟิกในหน่วยความจำทันที
        from config import load_config_from_db
        load_config_from_db()
        
        messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลร้านสำเร็จ!")
    
    def save_tax_settings(self):
        """บันทึกการตั้งค่าภาษี"""
        try:
            vat = float(self.vat_entry.get()) / 100
            
            self.db.connect()
            self.db.execute("""
                INSERT INTO settings (setting_key, setting_value)
                VALUES ('tax_rate', ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
            """, (str(vat), str(vat)))
            self.db.disconnect()
            
            # รีโหลดคอนฟิกในหน่วยความจำทันที
            from config import load_config_from_db
            load_config_from_db()
            
            messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่าสำเร็จ!")
        except ValueError:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกอัตราภาษีที่ถูกต้อง")
    
    def save_receipt_settings(self):
        """บันทึกการตั้งค่าใบเสร็จ"""
        message = self.receipt_message.get("1.0", "end").strip()
        
        settings = {
            'receipt_message': message,
            'receipt_show_barcode': str(self.show_barcode_var.get()),
            'receipt_show_cashier': str(self.show_cashier_var.get()),
            'receipt_auto_print': str(self.auto_print_var.get()),
        }
        
        self.db.connect()
        for key, value in settings.items():
            self.db.execute("""
                INSERT INTO settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
            """, (key, value, value))
        self.db.disconnect()
        
        # รีโหลดคอนฟิกในหน่วยความจำทันที
        from config import load_config_from_db
        load_config_from_db()
        
        messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่าใบเสร็จสำเร็จ!")
    
    def save_printer_settings(self):
        """บันทึกการตั้งค่าเครื่องพิมพ์"""
        settings = {
            'printer_type': self.printer_type_var.get(),
            'printer_name': self.printer_name_var.get(),
            'paper_size': self.paper_size_var.get(),
        }
        
        self.db.connect()
        for key, value in settings.items():
            self.db.execute("""
                INSERT INTO settings (setting_key, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?
            """, (key, value, value))
        self.db.disconnect()
        
        # รีโหลดคอนฟิกในหน่วยความจำทันที
        from config import load_config_from_db
        load_config_from_db()
        
        messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่าเครื่องพิมพ์สำเร็จ!")
    
    def load_available_printers(self):
        """โหลดรายชื่อเครื่องพิมพ์ที่มีในระบบ"""
        try:
            from utils import get_printers
            printers = get_printers()
            
            if printers:
                self.printer_combo.configure(values=printers)
                if printers and not self.printer_name_var.get():
                    self.printer_name_var.set(printers[0])
            else:
                self.printer_combo.configure(values=["ไม่พบเครื่องพิมพ์"])
                messagebox.showwarning("แจ้งเตือน", "ไม่พบเครื่องพิมพ์ในระบบ")
        except Exception as e:
            self.printer_combo.configure(values=["เกิดข้อผิดพลาด"])
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดรายชื่อเครื่องพิมพ์ได้:\n{e}")
    
    def test_print(self):
        """ทดสอบพิมพ์ — จำลองใบเสร็จทันทีตามประเภทและขนาดกระดาษที่เลือก"""
        import threading
        import os
        from pathlib import Path

        printer_type = self.printer_type_var.get()
        paper_size = self.paper_size_var.get()
        printer_name = self.printer_name_var.get()

        # ข้อมูลใบเสร็จจำลอง (สมจริง)
        test_data = {
            'sale_number': f'TEST-{datetime.now().strftime("%H%M%S")}',
            'sale_date': datetime.now().strftime(DATETIME_FORMAT),
            'cashier': 'พนักงานทดสอบ',
            'customer_name': 'ลูกค้าทดสอบ',
            'items': [
                {'product_name': 'น้ำดื่มตราช้าง 600ml', 'quantity': 3, 'unit_price': 10.00, 'total_price': 30.00},
                {'product_name': 'มาม่าต้มยำกุ้ง', 'quantity': 5, 'unit_price': 7.00, 'total_price': 35.00},
                {'product_name': 'ขนมปังแผ่น (ยาว)', 'quantity': 1, 'unit_price': 35.00, 'total_price': 35.00},
                {'product_name': 'นมโฟร์โมส UHT 250ml', 'quantity': 2, 'unit_price': 18.00, 'total_price': 36.00},
                {'product_name': 'สบู่ก้อน Lux', 'quantity': 1, 'unit_price': 25.00, 'total_price': 25.00},
            ],
            'subtotal': 161.00,
            'discount_amount': 11.00,
            'tax_amount': 10.50,
            'total_amount': 150.00,
            'paid_amount': 200.00,
            'change_amount': 50.00,
            'company': COMPANY_INFO,
        }

        def do_test():
            try:
                from utils.pdf_utils import create_receipt_pdf

                # สร้างโฟลเดอร์ temp
                temp_dir = Path("data/temp")
                temp_dir.mkdir(parents=True, exist_ok=True)
                out_path = temp_dir / f"test_receipt_{test_data['sale_number']}.pdf"

                # สร้าง PDF ตามขนาดกระดาษที่เลือก
                ok = create_receipt_pdf(test_data, str(out_path), paper_size=paper_size)

                if ok and out_path.exists():
                    # เปิดทันที — ไม่ว่าจะเลือกประเภทไหน
                    os.startfile(str(out_path))
                    # แจ้งผลใน main thread
                    self.after(100, lambda: messagebox.showinfo(
                        "✅ ทดสอบสำเร็จ",
                        f"จำลองใบเสร็จสำเร็จ!\n\n"
                        f"ประเภท: {printer_type.upper()}\n"
                        f"ขนาดกระดาษ: {paper_size}\n"
                        f"เครื่องพิมพ์: {printer_name or '(ค่าเริ่มต้น)'}\n\n"
                        f"ไฟล์: {out_path.name}"
                    ))
                else:
                    self.after(100, lambda: messagebox.showerror(
                        "ผิดพลาด", "ไม่สามารถสร้างใบเสร็จตัวอย่างได้\nตรวจสอบ log ที่ printer_debug.log"
                    ))
            except Exception as e:
                self.after(100, lambda err=e: messagebox.showerror(
                    "ข้อผิดพลาด", f"เกิดข้อผิดพลาด:\n{err}"
                ))

        # รันใน thread แยก — UI ไม่ค้าง
        threading.Thread(target=do_test, daemon=True).start()
    
    def backup_database(self):
        """สำรองข้อมูล"""
        # เลือกตำแหน่งบันทึก
        filename = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )
        
        if not filename:
            return
        
        try:
            import zipfile
            import sqlite3
            from config import DATABASE_PATH
            
            # Flush WAL log เข้าไฟล์หลักก่อนสำรอง (ป้องกันข้อมูลล่าสุดหายจาก WAL mode)
            try:
                _bk_conn = sqlite3.connect(DATABASE_PATH)
                _bk_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                _bk_conn.close()
            except Exception:
                pass  # ถ้า checkpoint ไม่ได้ก็ยังสำรองไปก่อน
            
            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # ฐานข้อมูล
                db_path_file = Path(DATABASE_PATH)
                if db_path_file.exists():
                    zipf.write(str(db_path_file), "database.db")
                
                # รูปภาพสินค้า (ใช้ PRODUCTS_IMG_DIR จาก config — BUG-011)
                img_dir = PRODUCTS_IMG_DIR
                if img_dir.exists():
                    for img_file in img_dir.glob("*"):
                        if img_file.is_file():
                            zipf.write(img_file, f"products_img/{img_file.name}")
                
                # ใบเสร็จ
                receipt_dir = Path("data/receipts")
                if receipt_dir.exists():
                    for receipt_file in receipt_dir.glob("*.pdf"):
                        zipf.write(receipt_file, f"receipts/{receipt_file.name}")
            
            messagebox.showinfo(
                "สำเร็จ",
                f"สำรองข้อมูลสำเร็จ!\n\nบันทึกที่: {filename}"
            )
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถสำรองข้อมูลได้: {e}")
    
    def restore_database(self):
        """กู้คืนข้อมูล"""
        result = messagebox.askyesno(
            "ยืนยัน",
            "การกู้คืนจะเขียนทับข้อมูลปัจจุบัน\nต้องการดำเนินการต่อหรือไม่?"
        )
        
        if not result:
            return
        
        filename = filedialog.askopenfilename(
            filetypes=[("ZIP files", "*.zip")],
            title="เลือกไฟล์สำรองข้อมูล"
        )
        
        if not filename:
            return
        
        try:
            import zipfile
            
            with zipfile.ZipFile(filename, 'r') as zipf:
                # แตก zip
                zipf.extractall("data/restore_temp")
            
            # ย้ายไฟล์
            temp_dir = Path("data/restore_temp")
            
            # ปิด connection ก่อนกู้คืน
            type(self.db).close_all_connections()
            from config import DATABASE_PATH
            
            # ลบไฟล์ WAL และ SHM เพื่อป้องกันฐานข้อมูลพังจากการกู้คืนในโหมด WAL (WAL corruption)
            try:
                db_wal = Path(DATABASE_PATH).with_name(Path(DATABASE_PATH).name + "-wal")
                db_shm = Path(DATABASE_PATH).with_name(Path(DATABASE_PATH).name + "-shm")
                if db_wal.exists():
                    db_wal.unlink()
                if db_shm.exists():
                    db_shm.unlink()
            except Exception as e:
                print(f"Error removing WAL/SHM files during restore: {e}")
            
            # รองรับทั้ง backup แบบใหม่ (database.db) และแบบเก่า (sales.db)
            if (temp_dir / "database.db").exists():
                shutil.copy(temp_dir / "database.db", DATABASE_PATH)
            elif (temp_dir / "sales.db").exists():
                shutil.copy(temp_dir / "sales.db", DATABASE_PATH)
            
            # คืนรูปภาพสินค้า (BUG-012)
            img_restore_dir = temp_dir / "products_img"
            if img_restore_dir.exists():
                dest_img_dir = PRODUCTS_IMG_DIR
                dest_img_dir.mkdir(parents=True, exist_ok=True)
                for img_file in img_restore_dir.iterdir():
                    shutil.copy(img_file, dest_img_dir / img_file.name)
            
            # คืนใบเสร็จ (BUG-012)
            receipt_restore_dir = temp_dir / "receipts"
            if receipt_restore_dir.exists():
                dest_receipt_dir = Path("data/receipts")
                dest_receipt_dir.mkdir(parents=True, exist_ok=True)
                for receipt_file in receipt_restore_dir.iterdir():
                    shutil.copy(receipt_file, dest_receipt_dir / receipt_file.name)
            
            # ลบ temp
            shutil.rmtree(temp_dir)
            
            messagebox.showinfo(
                "สำเร็จ",
                "กู้คืนข้อมูลสำเร็จ!\nกรุณาปิดโปรแกรมและเปิดใหม่"
            )
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถกู้คืนข้อมูลได้: {e}")
    
    def clear_login_history(self):
        """ล้างประวัติการล็อกอิน"""
        result = messagebox.askyesno(
            "ยืนยัน",
            "ต้องการล้างประวัติการล็อกอินทั้งหมดหรือไม่?"
        )
        
        if result:
            self.db.connect()
            self.db.execute("DELETE FROM login_history")
            self.db.disconnect()
            
            messagebox.showinfo("สำเร็จ", "ล้างประวัติการล็อกอินสำเร็จ")
    
    def clear_parked_sales(self):
        """ล้างการขายที่พัก"""
        result = messagebox.askyesno(
            "ยืนยัน",
            "ต้องการล้างการขายที่พักทั้งหมดหรือไม่?"
        )
        
        if result:
            self.db.connect()
            self.db.execute("DELETE FROM parked_sales")
            self.db.disconnect()
            
            messagebox.showinfo("สำเร็จ", "ล้างการขายที่พักสำเร็จ")
    
    def reset_system(self):
        """รีเซ็ตระบบ — ยืนยัน 2 ครั้ง (ไม่ต้องพิมพ์พาสเวิร์ด)"""
        # ถามครั้งที่ 1
        result = messagebox.askyesno(
            "⚠️ คำเตือน!",
            "การรีเซ็ตจะลบข้อมูลทั้งหมด!\n"
            "รวมถึง: สินค้า, ยอดขาย, ประวัติ, ผู้ใช้\n\n"
            "คุณแน่ใจหรือไม่?",
            icon="warning"
        )
        
        if not result:
            return
        
        # ถามครั้งที่ 2 — ย้ำชัดเจน
        confirm = messagebox.askyesno(
            "⚠️ ยืนยันครั้งสุดท้าย!",
            "ข้อมูลทั้งหมดจะถูกลบถาวร ไม่สามารถกู้คืนได้!\n\n"
            "กรุณากด 'Yes' เพื่อยืนยันการรีเซ็ต\n"
            "หรือกด 'No' เพื่อยกเลิก",
            icon="warning"
        )
        
        if confirm:
            try:
                # ปิดทุก connection ก่อนลบไฟล์ (ลดโอกาสการเกิด PermissionError/WinError 32)
                type(self.db).close_all_connections()

                # ลบฐานข้อมูล
                db_path = Path("data/sales.db")
                if db_path.exists():
                    db_path.unlink()
                
                # ลบ database หลักด้วย
                from config import DATABASE_PATH
                if Path(DATABASE_PATH).exists():
                    Path(DATABASE_PATH).unlink()
                
                messagebox.showinfo(
                    "สำเร็จ",
                    "รีเซ็ตระบบสำเร็จ!\nกรุณาปิดโปรแกรมและเปิดใหม่"
                )
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถรีเซ็ตได้: {e}")
