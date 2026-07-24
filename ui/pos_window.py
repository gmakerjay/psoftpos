# -*- coding: utf-8 -*-
"""
หน้าขายสินค้า (POS - Point of Sale)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from database import DatabaseManager
from utils import create_receipt_pdf, SalesLogManager, print_receipt, bind_english_input, kick_cash_drawer, translate_thai_barcode
from config import *
from datetime import datetime
import json
from utils.logger import log_user_action, log_sale, log_error, log_info


class POSFrame(ctk.CTkFrame):
    """Frame สำหรับขายสินค้า - Optimized for low-end computers"""
    
    def __init__(self, parent, user_id, user_info):
        super().__init__(parent, fg_color=COLORS["light"])
        self.root_window = parent.winfo_toplevel()
        self.user_id = user_id
        self.user_info = user_info
        self.db = DatabaseManager()
        self.slm = SalesLogManager()
        
        # ตัวแปรสำหรับจัดการหลายหน้าขาย (Sessions)
        self.sessions = []
        self.active_session_index = 0
        
        # สร้าง session แรก
        self.add_new_session(initial=True)
        
        # Performance optimization: Cache
        self._products_cache = {}  # Cache สินค้าที่ค้นหาบ่อย
        self._cache_time = None
        self._autocomplete_data = []  # ข้อมูลสำหรับ autocomplete
        self._suggestion_visible = False  # สถานะ dropdown ค้นหาอัจฉริยะ
        self._suggestion_debounce_id = None  # debounce timer สำหรับลด CPU
        
        # สร้าง UI ก่อน
        self.create_widgets()
        self.load_members_dropdown()
        
        # จากนั้นค่อย update summary และโหลดข้อมูล
        self.update_summary()
        self.load_autocomplete_data()  # โหลดข้อมูล autocomplete ครั้งเดียว
        self.setup_keyboard_shortcuts()  # ตั้งค่า shortcuts
        
    def create_widgets(self):
        """สร้าง UI"""
        # แถบเลือกหน้าขาย (Tabs) อยู่ด้านบนสุด
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.tab_container.pack(fill="x", padx=20, pady=(10, 0))
        self.update_tabs_ui()
        
        # แบ่งหน้าจอเป็น 2 ส่วน
        # ซ้าย: ค้นหาและรายการสินค้า
        # ขวา: รายการขายและชำระเงิน
        
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=(10, 20))
        
        right_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=15, width=450)
        right_frame.pack(side="right", fill="y", padx=(10, 20), pady=(10, 20))
        right_frame.pack_propagate(False)
        
        self.create_left_panel(left_frame)
        self.create_right_panel(right_frame)
        
    def create_left_panel(self, parent):
        """สร้างแผงซ้าย - ค้นหาและเลือกสินค้า"""
        # Header with Customer Display button
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        header = ctk.CTkLabel(
            header_frame,
            text="💰 ขายสินค้า (POS)",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        header.pack(side="left")
        
        # Customer Display Button
        has_display = hasattr(self.root_window, 'customer_display') and self.root_window.customer_display and self.root_window.customer_display.winfo_exists()
        btn_text = "📺 ปิดจอลูกค้า" if has_display else "📺 เปิดจอลูกค้า"
        btn_color = COLORS["danger"] if has_display else COLORS["info"]

        self.display_btn = ctk.CTkButton(
            header_frame,
            text=btn_text,
            font=FONTS["button"],
            width=150,
            height=40,
            fg_color=btn_color,
            hover_color=COLORS["hover"],
            command=self.toggle_customer_display
        )
        self.display_btn.pack(side="right", padx=10)
        
        self.customer_display = self.root_window.customer_display if has_display else None
        
        # ช่องค้นหา
        search_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 15))
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=("Arial", 24)
        )
        search_label.pack(side="left", padx=15)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="สแกนบาร์โค้ดหรือค้นหาสินค้า...",
            font=FONTS["body"],
            height=50,
            border_width=0
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=15)
        self.search_entry.bind("<Return>", self._on_search_enter)
        self.search_entry.bind("<KeyRelease>", self._on_search_key_release)
        self.search_entry.bind("<Down>", self._suggestion_navigate)
        self.search_entry.bind("<Up>", self._suggestion_navigate)
        self.search_entry.bind("<Escape>", lambda e: self._hide_suggestions())
        self.search_entry.focus()
        # บังคับ EN input สำหรับปืนบาร์โค้ดทุกรุ่น แต่ยังยอมให้พิมพ์ไทยค้นหาได้
        bind_english_input(self.search_entry, allow_thai=True)
        
        # สร้าง Suggestion Dropdown (ซ่อนไว้จนกว่าจะพิมพ์)
        self._suggestion_frame = None
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="ค้นหา",
            font=FONTS["button"],
            width=100,
            height=40,
            fg_color=COLORS["primary"],
            command=self.search_product
        )
        search_btn.pack(side="left", padx=(0, 15))
        
        # ประเภทราคา (ตัดออกเหลือแค่ราคาปกติ)
        self.price_type_var = ctk.StringVar(value="retail")
        
        # รายการสินค้าที่พบ
        ctk.CTkLabel(
            parent,
            text="รายการสินค้า",
            font=FONTS["heading"],
            text_color=COLORS["text_dark"]
        ).pack(anchor="w", pady=(10, 10))
        
        self.products_list = ctk.CTkScrollableFrame(
            parent,
            fg_color="white",
            corner_radius=10
        )
        self.products_list.pack(fill="both", expand=True)
        
        # โหลดสินค้าทั้งหมด
        self.load_all_products()
        
    def add_new_session(self, initial=False):
        """เพิ่มหน้าขายใหม่"""
        session = {
            'cart_items': [],
            'price_type': "retail",
            'discount_type': "amount",
            'discount_value': 0,
            'vat_enabled': False,
            'vat_rate': TAX_RATE,
            'selected_member_id': None,
            'member_name': "-- เลือกสมาชิก --"
        }
        self.sessions.append(session)
        
        if not initial:
            self.switch_session(len(self.sessions) - 1)
        else:
            self.active_session_index = 0
            self.load_session_data(0)

    def save_current_session_data(self):
        """บันทึกข้อมูลหน้าขายปัจจุบันลงในลิสต์ sessions"""
        if 0 <= self.active_session_index < len(self.sessions):
            self.sessions[self.active_session_index] = {
                'cart_items': self.cart_items,
                'price_type': "retail", # ปัจจุบัน POS นี้ล็อคที่ retail ใน UI
                'discount_type': self.discount_type_combo.get() if hasattr(self, 'discount_type_combo') else "บาท",
                'discount_value': float(self.discount_entry.get()) if hasattr(self, 'discount_entry') and self.discount_entry.get() else 0,
                'vat_enabled': self.vat_enabled,
                'vat_rate': self.vat_rate,
                'selected_member_id': self.selected_member_id if hasattr(self, 'selected_member_id') else None,
                'member_name': self.member_var.get() if hasattr(self, 'member_var') else "-- เลือกสมาชิก --"
            }

    def load_session_data(self, index):
        """โหลดข้อมูลหน้าขายจากลิสต์ sessions มายังตัวแปรหลัก"""
        session = self.sessions[index]
        self.cart_items = session['cart_items']
        self.price_type = session['price_type']
        self.discount_type = session['discount_type']
        self.discount_value = session['discount_value']
        self.vat_enabled = session['vat_enabled']
        self.vat_rate = session['vat_rate']
        self.selected_member_id = session.get('selected_member_id', None)
        
        # อัปเดต UI widgets ถ้าถูกสร้างแล้ว
        if hasattr(self, 'discount_entry'):
            self.discount_entry.delete(0, 'end')
            self.discount_entry.insert(0, str(int(self.discount_value) if self.discount_value == int(self.discount_value) else self.discount_value))
            self.discount_type_combo.set(self.discount_type if self.discount_type in ["บาท", "%"] else "บาท")
            
            if hasattr(self, 'member_combo'):
                self.member_var.set(session.get('member_name', "-- เลือกสมาชิก --"))
                if hasattr(self, 'member_privilege_label'):
                    if self.selected_member_id:
                        try:
                            self.db.connect()
                            m = self.db.fetch_one("SELECT privilege, points FROM members WHERE member_id = ?", (self.selected_member_id,))
                            self.db.disconnect()
                            priv = m['privilege'] if m else None
                            pts = m['points'] if m else 0
                            self.member_privilege_label.configure(text=f"🎁 สิทธิ์: {priv or 'ไม่มีสิทธิพิเศษ'} | 🪙 แต้มสะสม: {pts} แต้ม")
                        except:
                            self.member_privilege_label.configure(text="")
                    else:
                        self.member_privilege_label.configure(text="")
                
            if self.vat_enabled:
                self.vat_checkbox.select()
            else:
                self.vat_checkbox.deselect()
                
            self.vat_entry.delete(0, 'end')
            self.vat_entry.insert(0, str(int(self.vat_rate * 100)))

    def switch_session(self, index):
        """สลับไปหน้าขายที่ระบุ"""
        if index == self.active_session_index:
            return
            
        self.save_current_session_data()
        self.active_session_index = index
        self.load_session_data(index)
        
        # รีเฟรช UI
        self.update_tabs_ui()
        self.update_cart_display()
        self.update_summary()
        self.search_entry.focus()

    def remove_session(self, index):
        """ลบหน้าขาย"""
        if len(self.sessions) <= 1:
            messagebox.showwarning("แจ้งเตือน", "ไม่สามารถลบหน้าขายสุดท้ายได้")
            return
            
        if self.sessions[index]['cart_items']:
            if not messagebox.askyesno("ยืนยัน", "หน้าขายนี้มีสินค้าอยู่ ต้องการลบหรือไม่?"):
                return
                
        self.sessions.pop(index)
        
        # ปรับ index ปัจจุบัน
        if index <= self.active_session_index:
            self.active_session_index = max(0, self.active_session_index - 1)
            
        self.load_session_data(self.active_session_index)
        self.update_tabs_ui()
        self.update_cart_display()
        self.update_summary()

    def update_tabs_ui(self):
        """อัปเดต UI ของแถบเลือกหน้าขาย"""
        if not hasattr(self, 'tab_container'):
            return
            
        for widget in self.tab_container.winfo_children():
            widget.destroy()
            
        for i, session in enumerate(self.sessions):
            is_active = (i == self.active_session_index)
            
            tab_frame = ctk.CTkFrame(
                self.tab_container, 
                fg_color=COLORS["primary"] if is_active else "white",
                corner_radius=10,
                border_width=1 if not is_active else 0,
                border_color=COLORS["border"]
            )
            tab_frame.pack(side="left", padx=5)
            
            # ปุ่มสลับหน้า
            items_count = len(session['cart_items'])
            tab_btn = ctk.CTkButton(
                tab_frame,
                text=f"ลูกค้า {i+1} ({items_count})",
                font=("Sarabun", 13, "bold") if is_active else ("Sarabun", 13),
                fg_color="transparent",
                text_color="white" if is_active else COLORS["text_dark"],
                hover_color=COLORS["secondary"] if is_active else COLORS["light"],
                width=120,
                command=lambda idx=i: self.switch_session(idx)
            )
            tab_btn.pack(side="left", padx=(5, 0), pady=2)
            
            # ปุ่มกากบาทลบ tab
            if len(self.sessions) > 1:
                close_btn = ctk.CTkButton(
                    tab_frame,
                    text="✕",
                    width=20,
                    height=20,
                    font=("Arial", 10, "bold"),
                    fg_color="transparent",
                    text_color="white" if is_active else COLORS["danger"],
                    hover_color="#ff4d4f" if is_active else "#fff1f0",
                    command=lambda idx=i: self.remove_session(idx)
                )
                close_btn.pack(side="left", padx=(0, 5))
                
        # ปุ่มเพิ่มหน้าขายใหม่
        add_btn = ctk.CTkButton(
            self.tab_container,
            text="+ เพิ่มหน้าขาย",
            font=FONTS["small"],
            width=100,
            height=34,
            fg_color="white",
            text_color=COLORS["primary"],
            border_width=1,
            border_color=COLORS["primary"],
            hover_color=COLORS["light"],
            command=self.add_new_session
        )
        add_btn.pack(side="left", padx=10)
        
    def create_right_panel(self, parent):
        """สร้างแผงขวา - รายการขายและชำระเงิน"""
        # Header
        header_frame = ctk.CTkFrame(parent, fg_color=COLORS["primary"], corner_radius=0)
        header_frame.pack(fill="x")
        
        ctk.CTkLabel(
            header_frame,
            text="รายการสินค้าในตะกร้า",
            font=FONTS["heading"],
            text_color="white"
        ).pack(pady=15)
        
        # รายการในตะกร้า (Dynamic height for responsive UI)
        self.cart_list = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS["light"],
            corner_radius=0
        )
        # Packed at the end of create_right_panel
        
        # ค้นหาและเลือกสมาชิก
        member_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=0)
        member_frame.pack(side="bottom", fill="x", padx=15, pady=(5, 5))
        
        ctk.CTkLabel(
            member_frame,
            text="สมาชิก:",
            font=FONTS["body"]
        ).pack(side="left", padx=(0, 5))
        
        self.member_search_entry = ctk.CTkEntry(
            member_frame,
            placeholder_text="ค้นชื่อ/เบอร์...",
            font=FONTS["body"],
            width=100,
            height=35
        )
        self.member_search_entry.pack(side="left", padx=2)
        self.member_search_entry.bind("<Return>", self.search_member_pos)
        
        self.member_search_btn = ctk.CTkButton(
            member_frame,
            text="🔍",
            font=FONTS["body"],
            width=35,
            height=35,
            fg_color=COLORS["primary"],
            command=self.search_member_pos
        )
        self.member_search_btn.pack(side="left", padx=2)
        
        self.member_var = ctk.StringVar(value="-- เลือกสมาชิก --")
        self.member_combo = ctk.CTkComboBox(
            member_frame,
            values=["-- เลือกสมาชิก --"],
            variable=self.member_var,
            width=160,
            height=35,
            font=FONTS["body"],
            state="readonly",
            command=self.on_member_selected
        )
        self.member_combo.pack(side="left", padx=5)
        
        self.member_privilege_label = ctk.CTkLabel(
            member_frame,
            text="",
            font=("Sarabun", 12, "bold"),
            text_color=COLORS["success"]
        )
        self.member_privilege_label.pack(side="left", padx=15)
        
        # ส่วนลด
        discount_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=0)
        discount_frame.pack(side="bottom", fill="x", padx=15, pady=(0, 5))
        
        ctk.CTkLabel(
            discount_frame,
            text="ส่วนลด:",
            font=FONTS["body"]
        ).pack(side="left", padx=(0, 10))
        
        self.discount_entry = ctk.CTkEntry(
            discount_frame,
            width=100,
            height=35,
            font=FONTS["body"]
        )
        self.discount_entry.pack(side="left", padx=5)
        self.discount_entry.insert(0, "0")
        self.discount_entry.bind("<KeyRelease>", lambda e: self.update_summary())
        
        self.discount_type_combo = ctk.CTkComboBox(
            discount_frame,
            values=["บาท", "%"],
            width=70,
            height=35,
            font=FONTS["body"],
            state="readonly",
            command=lambda v: self.update_summary()
        )
        self.discount_type_combo.pack(side="left", padx=5)
        self.discount_type_combo.set("บาท")
        
        # สรุปยอด
        summary_frame = ctk.CTkFrame(parent, fg_color=COLORS["light"], corner_radius=10)
        summary_frame.pack(side="bottom", fill="x", padx=15, pady=(0, 5))
        
        # ยอดรวม
        sum_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        sum_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            sum_frame,
            text="ยอดรวม:",
            font=FONTS["body"]
        ).pack(side="left")
        
        self.subtotal_label = ctk.CTkLabel(
            sum_frame,
            text="฿0.00",
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["text_dark"]
        )
        self.subtotal_label.pack(side="right")
        
        # ส่วนลด
        disc_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        disc_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(
            disc_frame,
            text="ส่วนลด:",
            font=FONTS["body"]
        ).pack(side="left")
        
        self.discount_label = ctk.CTkLabel(
            disc_frame,
            text="฿0.00",
            font=FONTS["body"],
            text_color=COLORS["danger"]
        )
        self.discount_label.pack(side="right")
        
        # ภาษี VAT (มีปุ่มควบคุม)
        vat_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        vat_frame.pack(fill="x", padx=15, pady=5)
        
        # ส่วนซ้าย: Label และ Checkbox
        vat_left_frame = ctk.CTkFrame(vat_frame, fg_color="transparent")
        vat_left_frame.pack(side="left")
        
        self.vat_checkbox = ctk.CTkCheckBox(
            vat_left_frame,
            text="",
            width=20,
            checkbox_width=20,
            checkbox_height=20,
            command=self.toggle_vat
        )
        self.vat_checkbox.pack(side="left")
        # self.vat_checkbox.select()  # ปิดโดยเริ่มต้นตามต้องการ
        
        # self.vat_label_text = ctk.CTkLabel(
        #     vat_left_frame,
        #     text=f"ภาษี VAT",
        #     font=FONTS["body"]
        # )
        # self.vat_label_text.pack(side="left", padx=(5, 0))
        
        # ช่องแก้ไข VAT %
        vat_input_frame = ctk.CTkFrame(vat_left_frame, fg_color="transparent")
        vat_input_frame.pack(side="left", padx=5)
        
        self.vat_entry = ctk.CTkEntry(
            vat_input_frame,
            width=50,
            height=25,
            font=FONTS["small"]
        )
        self.vat_entry.pack(side="left")
        self.vat_entry.insert(0, str(int(TAX_RATE * 100)))
        self.vat_entry.bind("<KeyRelease>", lambda e: self.update_vat_rate())
        
        ctk.CTkLabel(
            vat_input_frame,
            text="%",
            font=FONTS["small"]
        ).pack(side="left", padx=(2, 0))
        
        # ส่วนขวา: ยอดภาษี
        self.tax_label = ctk.CTkLabel(
            vat_frame,
            text="฿0.00",
            font=FONTS["body"],
            text_color=COLORS["text_dark"]
        )
        self.tax_label.pack(side="right")
        
        # เส้นแบ่ง
        separator = ctk.CTkFrame(summary_frame, fg_color=COLORS["border"], height=2)
        separator.pack(fill="x", padx=15, pady=10)
        
        # ยอดสุทธิ
        total_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        total_frame.pack(fill="x", padx=15, pady=(2, 6))
        
        ctk.CTkLabel(
            total_frame,
            text="ยอดสุทธิ:",
            font=("Sarabun", 16, "bold")
        ).pack(side="left")
        
        self.total_label = ctk.CTkLabel(
            total_frame,
            text="฿0.00",
            font=("Sarabun", 32, "bold"),
            text_color="#27ae60"  # สีเขียวเข้มขึ้น
        )
        self.total_label.pack(side="right")
        
        # แสดงรับเงิน/เงินทอนล่าสุด
        self.last_payment_frame = ctk.CTkFrame(summary_frame, fg_color="white", corner_radius=10)
        self.last_payment_frame.pack(fill="x", padx=15, pady=(0, 6))
        
        # แถวเงินรับ
        recv_row = ctk.CTkFrame(self.last_payment_frame, fg_color="transparent")
        recv_row.pack(fill="x", padx=10, pady=(3, 0))
        ctk.CTkLabel(recv_row, text="รับเงินล่าสุด:", font=FONTS["small"]).pack(side="left")
        self.last_paid_label = ctk.CTkLabel(recv_row, text="฿0.00", font=FONTS["body"])
        self.last_paid_label.pack(side="right")
        
        # แถวเงินทอน
        change_row = ctk.CTkFrame(self.last_payment_frame, fg_color="transparent")
        change_row.pack(fill="x", padx=10, pady=(0, 3))
        ctk.CTkLabel(change_row, text="เงินทอน:", font=FONTS["body"], text_color=COLORS["success"]).pack(side="left")
        self.last_change_label = ctk.CTkLabel(change_row, text="฿0.00", font=("Sarabun", 16, "bold"), text_color=COLORS["success"])
        self.last_change_label.pack(side="right")
        
        # ซ่อนไว้ก่อน
        self.last_payment_frame.pack_forget()

        # ปุ่มด้านล่าง
        btn_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=0)
        btn_frame.pack(side="bottom", fill="x", padx=15, pady=(5, 10))
        
        checkout_btn = ctk.CTkButton(
            btn_frame,
            text="💰 ชำระเงิน (F10)",
            font=("Sarabun", 16, "bold"),
            height=48,
            fg_color=COLORS["success"],
            hover_color="#45a049",
            command=self.show_checkout_dialog
        )
        checkout_btn.pack(fill="x", pady=2)
        
        # Pack cart_list at the top to consume remaining space
        self.cart_list.pack(side="top", fill="both", expand=True)

        
    def load_all_products(self):
        """โหลดสินค้าทั้งหมด (with LIMIT)"""
        # ล้างรายการเดิม
        for widget in self.products_list.winfo_children():
            widget.destroy()
        
        # ดึงข้อมูล (ใช้ LIMIT ตาม Performance Mode)
        limit = PERFORMANCE_MODE["items_per_page"] if PERFORMANCE_MODE["enabled"] else 50
        self.db.connect()
        products = self.db.fetch_all("""
            SELECT product_id, barcode, product_name, retail_price, 
                   wholesale_price, special_price1, special_price2,
                   stock_quantity, image_path
            FROM products 
            WHERE is_active = 1 AND stock_quantity > 0
            ORDER BY product_name
            LIMIT ?
        """, (limit,))
        self.db.disconnect()
        
        if not products:
            ctk.CTkLabel(
                self.products_list,
                text="ไม่มีสินค้าในระบบ",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            ).pack(pady=30)
            return
        
        # แสดงสินค้า
        for product in products:
            self.create_product_card(product)
    
    def load_members_dropdown(self):
        """โหลดรายชื่อสมาชิกใส่ใน combobox"""
        try:
            self.db.connect()
            members = self.db.fetch_all("SELECT member_id, name, phone FROM members ORDER BY name")
            self.db.disconnect()
            
            self._members_cache_pos = {f"{m['name']} ({m['phone'] or '-'})": m['member_id'] for m in members}
            values = ["-- เลือกสมาชิก --"] + list(self._members_cache_pos.keys())
            self.member_combo.configure(values=values)
            self.member_combo.set("-- เลือกสมาชิก --")
            self.selected_member_id = None
        except Exception as e:
            print(f"Error loading members in POS: {e}")
            
    def search_member_pos(self, event=None):
        """ค้นหาสมาชิกด้วยชื่อหรือเบอร์โทรในหน้า POS"""
        query = self.member_search_entry.get().strip()
        if not query:
            self.load_members_dropdown()
            return
            
        try:
            self.db.connect()
            members = self.db.fetch_all(
                "SELECT member_id, name, phone FROM members WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
                (f"%{query}%", f"%{query}%")
            )
            self.db.disconnect()
            
            if not members:
                messagebox.showinfo("ไม่พบสมาชิก", f"ไม่พบสมาชิกที่ตรงกับ: {query}")
                self.load_members_dropdown()
                return
                
            self._members_cache_pos = {f"{m['name']} ({m['phone'] or '-'})": m['member_id'] for m in members}
            values = ["-- เลือกสมาชิก --"] + list(self._members_cache_pos.keys())
            self.member_combo.configure(values=values)
            
            if len(members) == 1:
                selected_val = list(self._members_cache_pos.keys())[0]
                self.member_combo.set(selected_val)
                self.on_member_selected(selected_val)
            else:
                self.member_combo.set("-- เลือกสมาชิก --")
                self.selected_member_id = None
                if hasattr(self, 'member_privilege_label'):
                    self.member_privilege_label.configure(text="")
        except Exception as e:
            print(f"Error searching members in POS: {e}")
            
    def on_member_selected(self, val):
        """เมื่อเลือกสมาชิก คำนวณส่วนลดสมาชิกอัตโนมัติ"""
        if val == "-- เลือกสมาชิก --":
            self.selected_member_id = None
            if hasattr(self, 'member_privilege_label'):
                self.member_privilege_label.configure(text="")
            self.discount_entry.delete(0, 'end')
            self.discount_entry.insert(0, "0")
            self.discount_type_combo.set("บาท")
            self.update_summary()
            return
            
        member_id = self._members_cache_pos.get(val)
        if not member_id:
            return
            
        self.selected_member_id = member_id
        
        # ดึงรายละเอียดส่วนลดสมาชิก
        try:
            self.db.connect()
            m = self.db.fetch_one("""
                SELECT m.*, t.discount_percent as tier_discount
                FROM members m
                LEFT JOIN member_tiers t ON m.tier_id = t.tier_id
                WHERE m.member_id = ?
            """, (member_id,))
            self.db.disconnect()
            
            if not m:
                return
                
            # แสดงรายละเอียดสิทธิประโยชน์
            privilege = m['privilege'] or "ไม่มีสิทธิพิเศษ"
            points = m['points'] or 0
            if hasattr(self, 'member_privilege_label'):
                self.member_privilege_label.configure(text=f"🎁 สิทธิ์: {privilege} | 🪙 แต้มสะสม: {points} แต้ม")
                
            # คำนวณส่วนลด
            disc_type = m['discount_type']
            disc_val = m['discount_value']
            
            # ตรวจสอบส่วนลดชั่วคราว
            if m['discount_duration'] == 'temporary':
                current_date = datetime.now().strftime("%Y-%m-%d")
                start = m['discount_start_date']
                end = m['discount_end_date']
                if not (start and end and start <= current_date <= end):
                    # ถ้าหมดอายุแล้ว หรือไม่อยู่ในช่วง ให้เปลี่ยนกลับไปใช้ส่วนลดตามระดับ (Tier)
                    disc_type = "percent"
                    disc_val = m['tier_discount'] or 0.0
                    
            if disc_type == "none":
                # ใช้ส่วนลดตามระดับ (Tier)
                disc_type = "percent"
                disc_val = m['tier_discount'] or 0.0
                
            # ตั้งค่าช่องส่วนลด in UI
            self.discount_entry.delete(0, 'end')
            self.discount_entry.insert(0, str(int(disc_val) if disc_val == int(disc_val) else disc_val))
            
            if disc_type == "percent":
                self.discount_type_combo.set("%")
            else:
                self.discount_type_combo.set("บาท")
                
            self.update_summary()
            
        except Exception as e:
            print(f"Error applying member discount in POS: {e}")
            
    def create_product_card(self, product):
        """สร้างการ์ดสินค้า"""
        card = ctk.CTkFrame(self.products_list, fg_color=COLORS["light"], corner_radius=10)
        card.pack(fill="x", padx=5, pady=5)
        
        # ชื่อและราคา
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=product['product_name'],
            font=FONTS["body"],
            anchor="w"
        )
        name_label.pack(fill="x")
        
        # แสดงราคาตามประเภทที่เลือก
        price_type = self.price_type_var.get()
        price = product[f'{price_type}_price']
        
        price_label = ctk.CTkLabel(
            info_frame,
            text=f"฿{price:,.2f}",
            font=("Sarabun", 16, "bold"),
            text_color=COLORS["success"],
            anchor="w"
        )
        price_label.pack(fill="x")
        
        stock_label = ctk.CTkLabel(
            info_frame,
            text=f"คงเหลือ: {product['stock_quantity']} ชิ้น",
            font=FONTS["small"],
            text_color=COLORS["text_light"],
            anchor="w"
        )
        stock_label.pack(fill="x")
        
        # ปุ่มเพิ่มในตะกร้า
        add_btn = ctk.CTkButton(
            card,
            text="➕",
            font=("Arial", 20),
            width=50,
            height=50,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            command=lambda p=product: self.add_to_cart(p)
        )
        add_btn.pack(side="right", padx=10, pady=10)
    
    def search_product(self, event=None):
        """ค้นหาสินค้า - Optimized with caching"""
        search_text = self.search_entry.get().strip()
        search_text = translate_thai_barcode(search_text)
        
        if not search_text:
            self.load_all_products()
            return
        
        # ล้างรายการเดิม
        for widget in self.products_list.winfo_children():
            widget.destroy()
        
        # ตรวจสอบ cache ก่อน (ลด query ซ้ำ)
        cache_key = f"search_{search_text.lower()}"
        if cache_key in self._products_cache:
            cached_data = self._products_cache[cache_key]
            
            # กรณีเป็นสินค้าชิ้นเดียว (Exact Match)
            if not isinstance(cached_data, list):
                # เคย scan บาร์โค้ดนี้แล้ว -> เพิ่มสินค้าเลย
                self.add_to_cart(cached_data)
                self.search_entry.delete(0, 'end')
                
                # Auto Focus กลับที่ช่องค้นหาทันที
                self.after(10, lambda: self.search_entry.focus())
                return
            
            # กรณีเป็นรายการสินค้า (Search Results)
            products = cached_data
        else:
            # ค้นหาจาก database
            self.db.connect()
            
            # ลองหาจากบาร์โค้ดก่อน (exact match)
            product = self.db.fetch_one(
                "SELECT * FROM products WHERE barcode = ? AND is_active = 1",
                (search_text,)
            )
            
            if product:
                # เจอบาร์โค้ด ใส่ในตะกร้าเลย
                self.add_to_cart(product)
                self.search_entry.delete(0, 'end')
                self.db.disconnect()
                
                # เก็บข้อมูลสินค้าลง Cache
                self._products_cache[cache_key] = product
                
                # ไม่ต้อง reload รายการสินค้า (ประหยัด CPU — Performance)
                # self.load_all_products()  # ตัดออกเพื่อลดการกระพริบ
                
                # Auto Focus กลับที่ช่องค้นหาทันที
                self.after(10, lambda: self.search_entry.focus())
                return
            
            # ค้นหาจากชื่อ (เพิ่ม LIMIT สำหรับ performance)
            limit = PERFORMANCE_MODE["items_per_page"] if PERFORMANCE_MODE["enabled"] else 30
            products = self.db.fetch_all("""
                SELECT product_id, barcode, product_name, retail_price, 
                       wholesale_price, special_price1, special_price2,
                       stock_quantity, image_path
                FROM products 
                WHERE is_active = 1 
                AND (LOWER(product_name) LIKE ? OR LOWER(barcode) LIKE ?)
                AND stock_quantity > 0
                ORDER BY product_name
                LIMIT ?
            """, (f"%{search_text.lower()}%", f"%{search_text.lower()}%", limit))
            
            self.db.disconnect()
            
            # บันทึก cache (สูงสุด PRODUCTS_CACHE_SIZE หรือ 100 รายการ)
            max_cache_size = 100
            try:
                import performance_config
                max_cache_size = performance_config.PRODUCTS_CACHE_SIZE
            except ImportError:
                pass
            if len(self._products_cache) > max_cache_size:
                self._products_cache.clear()
            self._products_cache[cache_key] = products
        
        if not products:
            messagebox.showwarning("ไม่พบสินค้า", f"ไม่พบรหัสสินค้า: '{search_text}'")
            self.search_entry.delete(0, 'end')
            self.search_entry.focus()
            return
        
        # แสดงผล (ใช้ virtual scrolling ถ้ามากกว่า 20 รายการ)
        for product in products:
            self.create_product_card(product)
    
    def add_to_cart(self, product):
        """เพิ่มสินค้าในตะกร้า"""
        unit_price = product['retail_price']
        
        # ตรวจสอบว่ามีในตะกร้าแล้วหรือไม่
        found = False
        for item in self.cart_items:
            if item['product_id'] == product['product_id']:
                # ตรวจสอบสต็อก
                remaining = product['stock_quantity'] - item['quantity']
                if remaining <= 0:
                    messagebox.showwarning("แจ้งเตือน", "สินค้าในสต็อกไม่เพียงพอ")
                    return
                    
                # เพิ่มจำนวน
                item['quantity'] += 1
                item['total'] = item['quantity'] * item['unit_price']
                
                # แจ้งเตือนสินค้าเหลือน้อย
                new_remaining = product['stock_quantity'] - item['quantity']
                if new_remaining <= 3:
                    messagebox.showwarning("⚠️ สินค้าใกล้หมดขั้นวิกฤต", f"ขณะนี้ '{product['product_name']}' เหลือในสต็อกเพียง {new_remaining} ชิ้นเท่านั้น!")
                found = True
                break
        
        if not found:
            # ตรวจสอบสต็อกสำหรับชิ้นแรก
            if product['stock_quantity'] <= 0:
                messagebox.showwarning("แจ้งเตือน", "สินค้าหมดสต็อก")
                return
                
            # เพิ่มใหม่
            img_path = product['image_path'] if 'image_path' in product.keys() else None
            self.cart_items.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'quantity': 1,
                'unit_price': unit_price,
                'total': unit_price,
                'max_stock': product['stock_quantity'],
                'image_path': img_path
            })
            
            # แจ้งเตือนชิ้นแรก
            remaining = product['stock_quantity'] - 1
            if remaining <= 3:
                messagebox.showwarning("⚠️ สินค้าใกล้หมดขั้นวิกฤต", f"ขณะนี้ '{product['product_name']}' เหลือในสต็อกเพียง {remaining} ชิ้นเท่านั้น!")
        
        self.update_cart_display()
        self.update_summary()
        self.update_tabs_ui()  # อัปเดตจำนวนสินค้าบน tab
        self.update_customer_display()  # อัพเดทจอลูกค้า
    
    def update_cart_display(self):
        """อัพเดทการแสดงผลตะกร้า"""
        # ล้างรายการเดิม
        for widget in self.cart_list.winfo_children():
            widget.destroy()
        
        if not self.cart_items:
            ctk.CTkLabel(
                self.cart_list,
                text="ไม่มีสินค้าในตะกร้า",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            ).pack(pady=30)
            return
        
        # แสดงรายการ
        for idx, item in enumerate(self.cart_items):
            item_frame = ctk.CTkFrame(
                self.cart_list,
                fg_color="white",
                corner_radius=8
            )
            item_frame.pack(fill="x", padx=5, pady=5)
            
            # ชื่อสินค้า
            name_label = ctk.CTkLabel(
                item_frame,
                text=item['product_name'],
                font=FONTS["body"],
                anchor="w"
            )
            name_label.pack(fill="x", padx=10, pady=(10, 5))
            
            # จำนวนและราคา
            detail_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            detail_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # ปุ่มลด
            minus_btn = ctk.CTkButton(
                detail_frame,
                text="-",
                width=30,
                height=30,
                font=("Arial", 16, "bold"),
                fg_color=COLORS["danger"],
                command=lambda i=idx: self.decrease_quantity(i)
            )
            minus_btn.pack(side="left", padx=2)
            
            # จำนวน
            qty_label = ctk.CTkLabel(
                detail_frame,
                text=str(item['quantity']),
                font=FONTS["body"],
                width=40
            )
            qty_label.pack(side="left", padx=5)
            
            # ปุ่มเพิ่ม
            plus_btn = ctk.CTkButton(
                detail_frame,
                text="+",
                width=30,
                height=30,
                font=("Arial", 16, "bold"),
                fg_color=COLORS["success"],
                command=lambda i=idx: self.increase_quantity(i)
            )
            plus_btn.pack(side="left", padx=2)
            
            # ราคารวม
            total_label = ctk.CTkLabel(
                detail_frame,
                text=f"฿{item['total']:,.2f}",
                font=("Sarabun", 16, "bold"),
                text_color=COLORS["success"]
            )
            total_label.pack(side="right")
            
            # ปุ่มลบ
            delete_btn = ctk.CTkButton(
                detail_frame,
                text="🗑️",
                width=30,
                height=30,
                font=("Arial", 14),
                fg_color=COLORS["danger"],
                command=lambda i=idx: self.remove_from_cart(i)
            )
            delete_btn.pack(side="right", padx=5)
    
    def increase_quantity(self, index):
        """เพิ่มจำนวนสินค้า"""
        item = self.cart_items[index]
        if item['quantity'] < item['max_stock']:
            item['quantity'] += 1
            item['total'] = item['quantity'] * item['unit_price']
            self.update_cart_display()
            self.update_summary()
            self.update_tabs_ui()  # อัปเดตจำนวนสินค้าบน tab
        else:
            messagebox.showwarning("แจ้งเตือน", "สินค้าในสต็อกไม่เพียงพอ")
    
    def decrease_quantity(self, index):
        """ลดจำนวนสินค้า"""
        item = self.cart_items[index]
        if item['quantity'] > 1:
            item['quantity'] -= 1
            item['total'] = item['quantity'] * item['unit_price']
            self.update_cart_display()
            self.update_summary()
            self.update_tabs_ui()  # อัปเดตจำนวนสินค้าบน tab
        else:
            self.remove_from_cart(index)
    
    def remove_from_cart(self, index):
        """ลบสินค้าออกจากตะกร้า"""
        del self.cart_items[index]
        self.update_cart_display()
        self.update_summary()
        self.update_tabs_ui()  # อัปเดตจำนวนสินค้าบน tab
    
    
    def update_summary(self):
        """อัพเดทสรุปยอด"""
        # คำนวณยอดรวม
        subtotal = sum(item['total'] for item in self.cart_items)
        
        # คำนวณส่วนลด
        try:
            discount_value = float(self.discount_entry.get())
        except:
            discount_value = 0
        
        discount_type = self.discount_type_combo.get()
        
        if discount_type == "%":
            discount_amount = (subtotal * discount_value) / 100
        else:
            discount_amount = discount_value
        
        # ยอดหลังหักส่วนลด
        after_discount = subtotal - discount_amount
        if after_discount < 0:
            after_discount = 0
        
        # ภาษี VAT (ใช้อัตราที่ตั้งไว้)
        if self.vat_enabled:
            tax_amount = after_discount * self.vat_rate
        else:
            tax_amount = 0
        
        # ยอดสุทธิ
        total = after_discount + tax_amount
        
        # อัพเดท UI
        self.subtotal_label.configure(text=f"฿{subtotal:,.2f}")
        self.discount_label.configure(text=f"฿{discount_amount:,.2f}")
        self.tax_label.configure(text=f"฿{tax_amount:,.2f}")
        self.total_label.configure(text=f"฿{total:,.2f}")
        
        # อัพเดท Customer Display (ถ้าเปิดอยู่)
        self.update_customer_display()
    
    def clear_cart(self):
        """ล้างตะกร้า"""
        if self.cart_items:
            result = messagebox.askyesno(
                "ยืนยัน",
                "ต้องการล้างรายการสินค้าทั้งหมดหรือไม่?"
            )
            if result:
                self.cart_items.clear()  # ใช้ .clear() แทน = [] เพื่อไม่ตัด reference จาก session (BUG-009)
                self.update_cart_display()
                self.update_summary()
                self.update_tabs_ui()  # อัปเดตจำนวนสินค้าบน tab
                if hasattr(self, 'last_payment_frame'):  # ป้องกัน crash ถ้ายังไม่ได้สร้าง (BUG-014)
                    self.last_payment_frame.pack_forget()
                self.update_customer_display()  # อัพเดทจอลูกค้า
                self.search_entry.focus()
    
    
    def show_checkout_dialog(self):
        """แสดงหน้าต่างชำระเงิน"""
        if not self.cart_items:
            messagebox.showwarning("แจ้งเตือน", "ไม่มีรายการสินค้าในตะกร้า")
            return
        
        # คำนวณยอดสุทธิ (ใช้ VAT settings)
        subtotal = sum(item['total'] for item in self.cart_items)
        
        try:
            discount_value = float(self.discount_entry.get())
        except:
            discount_value = 0
        
        discount_type = self.discount_type_combo.get()
        
        if discount_type == "%":
            discount_amount = (subtotal * discount_value) / 100
        else:
            discount_amount = discount_value
        
        after_discount = subtotal - discount_amount
        if after_discount < 0:
            after_discount = 0
        
        # ใช้ VAT settings แทน TAX_RATE
        if self.vat_enabled:
            tax_amount = after_discount * self.vat_rate
        else:
            tax_amount = 0
        
        total = after_discount + tax_amount
        
        # สร้างหน้าต่าง
        dialog = ctk.CTkToplevel(self)
        dialog.title("ชำระเงิน")
        
        target_h = 660 if self.selected_member_id else 540
        dialog.geometry(get_responsive_dialog_geometry(self, 520, target_h))
            
        dialog.transient(self)
        dialog.grab_set()
        
        # ยอดที่ต้องชำระ
        payable_label = ctk.CTkLabel(
            dialog,
            text=f"ยอดที่ต้องชำระ: ฿{total:,.2f}",
            font=("Sarabun", 24, "bold"),
            text_color=COLORS["success"]
        )
        payable_label.pack(pady=20)

        # ข้อมูลสมาชิกและแต้มสะสม
        points_used_var = ctk.StringVar(value="0")
        point_discount_var = ctk.StringVar(value="0")
        points_earned_var = ctk.StringVar(value=str(int(total // POINT_EARN_RATE)))
        member_points = 0
        if self.selected_member_id:
            try:
                self.db.connect()
                m_data = self.db.fetch_one("SELECT points, name FROM members WHERE member_id = ?", (self.selected_member_id,))
                self.db.disconnect()
                if m_data:
                    member_points = m_data['points'] or 0
                    member_name = m_data['name']
                    
                    # เฟรมข้อมูลแต้มสมาชิก
                    member_pts_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=8)
                    member_pts_frame.pack(fill="x", padx=50, pady=5)
                    
                    ctk.CTkLabel(
                        member_pts_frame,
                        text=f"👤 สมาชิก: {member_name} (แต้มที่มี: {member_points} แต้ม)",
                        font=FONTS["small"],
                        text_color=COLORS["text_dark"]
                    ).pack(pady=(5, 2))
                    
                    # แถวสำหรับกรอกแต้มที่ใช้ และ ส่วนลดที่ได้
                    pts_use_row = ctk.CTkFrame(member_pts_frame, fg_color="transparent")
                    pts_use_row.pack(fill="x", pady=(2, 2))
                    
                    ctk.CTkLabel(pts_use_row, text="ใช้แต้มสะสม:", font=FONTS["small"]).pack(side="left", padx=(10, 5))
                    pts_use_entry = ctk.CTkEntry(pts_use_row, textvariable=points_used_var, width=80, height=25, font=FONTS["small"], justify="center")
                    pts_use_entry.pack(side="left")
                    
                    ctk.CTkLabel(pts_use_row, text="แต้ม  คิดเป็นส่วนลด:", font=FONTS["small"]).pack(side="left", padx=(10, 5))
                    pts_disc_entry = ctk.CTkEntry(pts_use_row, textvariable=point_discount_var, width=80, height=25, font=FONTS["small"], justify="center")
                    pts_disc_entry.pack(side="left")
                    ctk.CTkLabel(pts_use_row, text="บาท", font=FONTS["small"]).pack(side="left", padx=2)
                    
                    # แถวสำหรับกรอกแต้มที่จะได้รับในบิลนี้
                    pts_earn_row = ctk.CTkFrame(member_pts_frame, fg_color="transparent")
                    pts_earn_row.pack(fill="x", pady=(2, 5))
                    
                    ctk.CTkLabel(pts_earn_row, text="แต้มที่ได้รับจากบิลนี้:", font=FONTS["small"]).pack(side="left", padx=(10, 5))
                    pts_earn_entry = ctk.CTkEntry(pts_earn_row, textvariable=points_earned_var, width=80, height=25, font=FONTS["small"], justify="center")
                    pts_earn_entry.pack(side="left")
                    ctk.CTkLabel(pts_earn_row, text="แต้ม", font=FONTS["small"]).pack(side="left", padx=2)
                    
                    # ตรวจสอบแต้มไม่ให้เกินแต้มที่มี และคำนวณส่วนลดโดยอัตโนมัติ (และป้องกัน loop)
                    def validate_points_use(*args):
                        try:
                            val = int(points_used_var.get() or 0)
                            if val < 0:
                                points_used_var.set("0")
                                val = 0
                            elif val > member_points:
                                points_used_var.set(str(member_points))
                                val = member_points
                                
                            discount_from_points = val * POINT_REDEEM_VALUE
                            if discount_from_points > total:
                                discount_from_points = total
                                val = int(total // POINT_REDEEM_VALUE)
                                points_used_var.set(str(val))
                                
                            try:
                                curr_disc = float(point_discount_var.get() or 0)
                            except:
                                curr_disc = 0.0
                                
                            if abs(curr_disc - discount_from_points) > 0.01:
                                point_discount_var.set(str(int(discount_from_points) if discount_from_points == int(discount_from_points) else discount_from_points))
                        except ValueError:
                            points_used_var.set("0")
                            point_discount_var.set("0")
                            
                    def validate_points_earned(*args):
                        try:
                            val = int(points_earned_var.get() or 0)
                            if val < 0:
                                points_earned_var.set("0")
                        except ValueError:
                            points_earned_var.set("0")
                            
                    points_used_var.trace_add("write", validate_points_use)
                    points_earned_var.trace_add("write", validate_points_earned)
            except Exception as e:
                print(f"Error loading member points in checkout: {e}")
        
        # ช่องทางชำระเงิน
        ctk.CTkLabel(
            dialog,
            text="ช่องทางชำระเงิน:",
            font=FONTS["body"]
        ).pack(pady=(10, 2))
        
        payment_method_combo = ctk.CTkComboBox(
            dialog,
            values=["เงินสด", "โอนเงิน", "QR Code", "จ่ายผสม (Mixed)"],
            font=FONTS["body"],
            height=35,
            width=250,
            state="readonly",
            command=lambda v: on_payment_method_change(v)
        )
        payment_method_combo.pack(pady=5)
        payment_method_combo.set("เงินสด")
        
        # เฟรมสำหรับรับเงินแบบเดี่ยว
        single_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        single_frame.pack(fill="x", padx=50)
        
        ctk.CTkLabel(
            single_frame,
            text="รับเงิน:",
            font=FONTS["heading"]
        ).pack(pady=(5, 2))
        
        paid_entry = ctk.CTkEntry(
            single_frame,
            font=("Sarabun", 20),
            height=45,
            justify="center"
        )
        paid_entry.pack(fill="x", pady=5)
        paid_entry.insert(0, str(total))
        paid_entry.select_range(0, 'end')
        paid_entry.focus()
        
        # เฟรมสำหรับรับเงินแบบผสม (เงินสด + โอน)
        mixed_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        
        ctk.CTkLabel(
            mixed_frame,
            text="จ่ายผสม (เงินสด + โอน/QR):",
            font=FONTS["body"]
        ).pack(pady=(5, 2))
        
        mixed_input_row = ctk.CTkFrame(mixed_frame, fg_color="transparent")
        mixed_input_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(mixed_input_row, text="เงินสด:", font=FONTS["body"]).pack(side="left", padx=5)
        cash_paid_entry = ctk.CTkEntry(mixed_input_row, font=("Sarabun", 16), height=35, width=120, justify="center")
        cash_paid_entry.pack(side="left", padx=5)
        cash_paid_entry.insert(0, "0")
        
        ctk.CTkLabel(mixed_input_row, text="โอน/QR:", font=FONTS["body"]).pack(side="left", padx=5)
        transfer_paid_entry = ctk.CTkEntry(mixed_input_row, font=("Sarabun", 16), height=35, width=120, justify="center")
        transfer_paid_entry.pack(side="left", padx=5)
        transfer_paid_entry.insert(0, str(total))
        
        def on_payment_method_change(val):
            if val == "จ่ายผสม (Mixed)":
                single_frame.pack_forget()
                mixed_frame.pack(fill="x", padx=50, pady=5)
                cash_paid_entry.focus()
                cash_paid_entry.select_range(0, 'end')
            else:
                mixed_frame.pack_forget()
                single_frame.pack(fill="x", padx=50, pady=5)
                paid_entry.focus()
                paid_entry.select_range(0, 'end')
            calculate_change()
            
        # เงินทอน
        change_label = ctk.CTkLabel(
            dialog,
            text="เงินทอน: ฿0.00",
            font=("Sarabun", 20, "bold"),
            text_color=COLORS["info"]
        )
        change_label.pack(pady=15)
        
        def on_point_discount_change(*args):
            try:
                pt_disc = float(point_discount_var.get() or 0)
            except ValueError:
                pt_disc = 0.0
            
            if pt_disc < 0:
                point_discount_var.set("0")
                pt_disc = 0.0
            elif pt_disc > total:
                pt_disc = total
                point_discount_var.set(str(int(total) if total == int(total) else total))
            
            # คำนวณแต้มที่ต้องแลกและอัปเดตแบบป้องกัน loop
            pts_needed = int(pt_disc // POINT_REDEEM_VALUE)
            if pts_needed > member_points:
                pts_needed = member_points
                pt_disc = pts_needed * POINT_REDEEM_VALUE
                point_discount_var.set(str(int(pt_disc) if pt_disc == int(pt_disc) else pt_disc))
                
            try:
                curr_pts = int(points_used_var.get() or 0)
            except:
                curr_pts = 0
                
            if curr_pts != pts_needed:
                points_used_var.set(str(pts_needed))
                
            current_total = max(0.0, total - pt_disc)
            payable_label.configure(text=f"ยอดที่ต้องชำระ: ฿{current_total:,.2f}")
            
            # อัปเดตแต้มที่จะได้รับโดยอัตโนมัติตามอัตราสะสมแต้ม
            points_earned_var.set(str(int(current_total // POINT_EARN_RATE)))
            
            # อัปเดตช่องรับเงิน
            method = payment_method_combo.get()
            if method != "จ่ายผสม (Mixed)":
                paid_entry.delete(0, 'end')
                paid_entry.insert(0, f"{current_total:.2f}")
            else:
                try:
                    c_val = float(cash_paid_entry.get() or 0)
                except:
                    c_val = 0.0
                transfer_paid_entry.delete(0, 'end')
                transfer_paid_entry.insert(0, f"{max(0.0, current_total - c_val):.2f}")
                
            calculate_change()

        def calculate_change(*args):
            try:
                try:
                    pt_disc = float(point_discount_var.get() or 0)
                except:
                    pt_disc = 0.0
                current_total = max(0.0, total - pt_disc)
                
                method = payment_method_combo.get()
                if method == "จ่ายผสม (Mixed)":
                    c_str = cash_paid_entry.get().strip()
                    t_str = transfer_paid_entry.get().strip()
                    c_val = float(c_str) if c_str else 0.0
                    t_val = float(t_str) if t_str else 0.0
                    paid = c_val + t_val
                else:
                    p_str = paid_entry.get().strip()
                    paid = float(p_str) if p_str else 0.0
                    
                change = paid - current_total
                if change < 0:
                    change_label.configure(
                        text=f"ยังขาดอีก: ฿{abs(change):,.2f}",
                        text_color=COLORS["danger"]
                    )
                else:
                    change_label.configure(
                        text=f"เงินทอน: ฿{change:,.2f}",
                        text_color=COLORS["success"]
                    )
                
                # อัพเดทที่หน้าจอหลัก
                self.last_payment_frame.pack(fill="x", padx=15, pady=(0, 10))
                self.last_paid_label.configure(text=f"฿{paid:,.2f}")
                self.last_change_label.configure(text=f"฿{max(0, change):,.2f}")
                
                # อัพเดทที่จอลูกค้า
                self.update_customer_display(paid=paid, change=change)
            except Exception as e:
                print(f"Error calculating change: {e}")
                change_label.configure(text="เงินทอน: ฿0.00")
        
        # ผูกฟังก์ชัน trace กับจุดเปลี่ยนแปลงส่วนลดแต้ม
        point_discount_var.trace_add("write", on_point_discount_change)
        
        paid_entry.bind("<KeyRelease>", calculate_change)
        cash_paid_entry.bind("<KeyRelease>", calculate_change)
        transfer_paid_entry.bind("<KeyRelease>", calculate_change)
        # เรียกครั้งแรกเพื่ออัพเดทจอ
        calculate_change()
        
        # ปุ่ม
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=50, pady=20)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="ยกเลิก",
            font=FONTS["button"],
            width=150,
            height=50,
            fg_color=COLORS["danger"],
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=10)
        
        def do_payment(event=None):
            import json
            method = payment_method_combo.get()
            method_db = "cash"
            details_db = None
            
            try:
                pt_disc = float(point_discount_var.get() or 0)
            except:
                pt_disc = 0.0
            current_total = max(0.0, total - pt_disc)
            
            if method == "โอนเงิน":
                method_db = "transfer"
            elif method == "QR Code":
                method_db = "qr"
            elif method == "จ่ายผสม (Mixed)":
                method_db = "mixed"
                try:
                    c_val = float(cash_paid_entry.get().strip() or 0)
                    t_val = float(transfer_paid_entry.get().strip() or 0)
                    paid_val = c_val + t_val
                    details_db = json.dumps({"cash": c_val, "transfer": t_val})
                except ValueError:
                    messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกจำนวนเงินให้ถูกต้อง")
                    return
            else:
                try:
                    paid_val = float(paid_entry.get().strip() or 0)
                except ValueError:
                    messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกจำนวนเงินให้ถูกต้อง")
                    return
                    
            points_used = 0
            points_earned = 0
            if self.selected_member_id:
                try:
                    points_used = int(points_used_var.get() or 0)
                except ValueError:
                    points_used = 0
                try:
                    points_earned = int(points_earned_var.get() or 0)
                except ValueError:
                    points_earned = 0
                    
            self.process_payment(
                dialog, current_total, subtotal, discount_amount + pt_disc, 
                tax_amount, str(paid_val), method_db, details_db, 
                points_used=points_used, points_earned=points_earned
            )

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="ยืนยันชำระเงิน",
            font=FONTS["button"],
            width=250,
            height=50,
            fg_color=COLORS["success"],
            command=do_payment
        )
        confirm_btn.pack(side="right", padx=10)
        
        # ผูกปุ่ม Enter ให้ชำระเงินทันที
        paid_entry.bind("<Return>", do_payment)
        cash_paid_entry.bind("<Return>", do_payment)
        transfer_paid_entry.bind("<Return>", do_payment)
        dialog.bind("<Return>", do_payment)
    
    def process_payment(self, dialog, total, subtotal, discount_amount, tax_amount, paid_str, payment_method="cash", payment_details=None, points_used=0, points_earned=0):
        """ประมวลผลการชำระเงิน"""
        try:
            paid = float(paid_str)
        except:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกจำนวนเงินที่ถูกต้อง")
            return
        
        if paid < total:
            messagebox.showwarning("แจ้งเตือน", "จำนวนเงินไม่เพียงพอ")
            return
        
        change = paid - total
            
        # บันทึกการขาย (ใช้ Transaction เพื่อความปลอดภัยของข้อมูล)
        self.db.connect()
        self.db.begin_transaction()
        
        try:
            sale_number = self.db.generate_sale_number()
            sale_date = datetime.now().strftime(DB_DATETIME_FORMAT)
            
            # บันทึกข้อมูลหลัก
            success = self.db.execute("""
                INSERT INTO sales (
                    sale_number, sale_date, user_id, price_type,
                    subtotal, discount_type, discount_value, discount_amount,
                    tax_amount, total_amount, paid_amount, change_amount,
                    payment_method, status, member_id, payment_details,
                    points_earned, points_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sale_number, sale_date, self.user_id, self.price_type,
                subtotal, self.discount_type_combo.get(), 
                self.discount_entry.get(), discount_amount,
                tax_amount, total, paid, change,
                payment_method, 'completed', self.selected_member_id, payment_details,
                points_earned, points_used
            ))
            
            if not success:
                raise Exception("ไม่สามารถบันทึกการขายได้")
            
            # ดึง sale_id
            sale = self.db.fetch_one(
                "SELECT sale_id FROM sales WHERE sale_number = ?",
                (sale_number,)
            )
            sale_id = sale['sale_id']
            
            # ปรับแต้มสมาชิกสะสม (หักแต้มที่ใช้ และ เพิ่มแต้มที่ได้รับ)
            if self.selected_member_id:
                self.db.execute(
                    "UPDATE members SET points = MAX(0, points - ? + ?) WHERE member_id = ?",
                    (points_used, points_earned, self.selected_member_id)
                )
            
            # บันทึกรายการสินค้า
            for item in self.cart_items:
                self.db.execute("""
                    INSERT INTO sale_items (
                        sale_id, product_id, product_name,
                        quantity, unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    sale_id, item['product_id'], item['product_name'],
                    item['quantity'], item['unit_price'], item['total']
                ))
                
                # ตัดสต็อก
                self.db.execute("""
                    UPDATE products 
                    SET stock_quantity = stock_quantity - ?
                    WHERE product_id = ?
                """, (item['quantity'], item['product_id']))
                
                # บันทึกการเคลื่อนไหวสต็อก
                self.db.execute("""
                    INSERT INTO stock_movements (
                        product_id, movement_type, quantity,
                        reference_id, reference_type, user_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item['product_id'], 'out', item['quantity'],
                    sale_id, 'sale', self.user_id, f'ขาย {sale_number}'
                ))
            
            # ทุกอย่างสำเร็จ — commit ทั้งหมด
            self.db.commit_transaction()
            self.db.disconnect()
            
            # บันทึก Log การขาย
            log_sale(sale_id, total, len(self.cart_items))
            log_user_action(self.user_id, "SALE", f"{sale_number} Total={total:,.2f} Paid={paid:,.2f} Change={change:,.2f}")
        except Exception as e:
            # ล้มเหลว — rollback ทั้งหมด (ข้อมูลไม่เปลี่ยน)
            self.db.rollback_transaction()
            self.db.disconnect()
            log_error(f"Payment failed for user {self.user_id}: {e}")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการขายได้:\n{e}")
            return
        
        # บันทึกลงไฟล์ .txt (Backup)
        self.slm.add_sale({
            "sale_number": sale_number,
            "total_amount": total,
            "payment_method": payment_method
        })
        
        # ปิดหน้าต่างชำระเงินทันที
        dialog.destroy()
        
        # ค้นหาชื่อสมาชิกมาแสดงบนใบเสร็จ
        customer_name = 'ลูกค้าทั่วไป'
        if self.selected_member_id:
            try:
                self.db.connect()
                m = self.db.fetch_one("SELECT name FROM members WHERE member_id = ?", (self.selected_member_id,))
                self.db.disconnect()
                if m:
                    customer_name = m['name']
            except:
                pass
                
        # เตรียมข้อมูลสำหรับพิมพ์
        receipt_data = {
            'company': COMPANY_INFO,
            'sale_number': sale_number,
            'sale_date': sale_date,
            'customer_name': customer_name,
            'cashier': self.user_info['full_name'] if self.user_info else 'พนักงาน',
            'items': [dict(item) for item in self.cart_items],
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'total_amount': total,
            'paid_amount': paid,
            'change_amount': change
        }
            
        # เช็คการตั้งค่าพิมพ์อัตโนมัติจากฐานข้อมูล
        auto_print = False
        try:
            self.db.connect()
            auto_print_setting = self.db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'receipt_auto_print'")
            self.db.disconnect()
            if auto_print_setting:
                auto_print = auto_print_setting['setting_value'] == 'True'
        except Exception as e:
            print(f"Error checking auto_print: {e}")
            
        if auto_print:
            # พิมพ์ใบเสร็จทันที
            try:
                print_receipt(receipt_data)
            except Exception as e:
                print(f"Auto print error: {e}")
            self.finalize_sale(paid, change)
        else:
            # ถามก่อนพิมพ์ (Popup)
            self.show_print_confirmation(receipt_data, paid, change)

    def show_print_confirmation(self, receipt_data, paid, change):
        """แสดงหน้าต่างยืนยันการพิมพ์ใบเสร็จ"""
        confirm_dialog = ctk.CTkToplevel(self)
        confirm_dialog.title("พิมพ์ใบเสร็จ")
        confirm_dialog.geometry("400x200")
        
        # ตั้งค่าให้เป็น Modal (อยู่บนสุดและบล็อคหน้าหลัง)
        confirm_dialog.transient(self)
        confirm_dialog.grab_set()
        confirm_dialog.attributes("-topmost", True)
        
        # จัดกึ่งกลางหน้าจอ (ประมาณการ)
        try:
            x = self.winfo_x() + (self.winfo_width() // 2) - 200
            y = self.winfo_y() + (self.winfo_height() // 2) - 100
            confirm_dialog.geometry(f"+{x}+{y}")
        except:
            pass # Fallback to default position
        
        # ข้อความ
        msg = ctk.CTkLabel(
            confirm_dialog, 
            text="ชำระเงินเสร็จสิ้น!\nต้องการพิมพ์ใบเสร็จหรือไม่?", 
            font=("Sarabun", 20, "bold"),
            text_color=COLORS["success"]
        )
        msg.pack(pady=(30, 20))
        
        btn_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def on_print(event=None):
            try:
                if not print_receipt(receipt_data):
                    messagebox.showerror("Error", "พิมพ์ไม่สำเร็จ")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            cleanup()
            
        def on_cancel(event=None):
            cleanup()
            
        def cleanup():
            confirm_dialog.destroy()
            self.finalize_sale(paid, change)
            
        # ปุ่ม
        btn_yes = ctk.CTkButton(
            btn_frame, 
            text="พิมพ์ (Enter)", 
            command=on_print, 
            fg_color=COLORS["success"],
            width=120,
            height=40,
            font=FONTS["button"]
        )
        btn_yes.pack(side="left", padx=10)
        
        btn_no = ctk.CTkButton(
            btn_frame, 
            text="ไม่พิมพ์ (Esc)", 
            command=on_cancel, 
            fg_color=COLORS["danger"],
            width=120,
            height=40,
            font=FONTS["button"]
        )
        btn_no.pack(side="left", padx=10)
        
        # Bindings
        confirm_dialog.bind("<Return>", on_print)
        confirm_dialog.bind("<KP_Enter>", on_print)
        confirm_dialog.bind("<Escape>", on_cancel)
        
        # Focus ที่ปุ่มพิมพ์
        btn_yes.focus()

    def finalize_sale(self, paid, change):
        """เคลียร์หน้าจอหลังขายจบ"""
        # ล้างตะกร้า (ใช้ .clear() เพื่อรักษา reference ของ session — BUG-009)
        self.cart_items.clear()
        self.update_cart_display()
        self.update_summary()
        self.update_tabs_ui()  # อัปเดตจำนวนสินค้าบน tab
        self.update_customer_display(paid=paid, change=change)  # อัพเดทจอลูกค้า (แสดงเงินทอน)
        
        # Clear cache เมื่อมีการขาย (เพื่อให้สต็อกอัพเดท)
        self._products_cache.clear()
        
        # เปิดลิ้นชักเงินสด (Cash Drawer Kick)
        if SALE_SETTINGS.get("open_cash_drawer", False):
            try:
                kick_cash_drawer()
            except Exception as e:
                print(f"Cash drawer kick error (non-critical): {e}")
        
        # Focus กลับไปที่ช่องค้นหา
        self.search_entry.focus()
    
    def load_autocomplete_data(self):
        """โหลดข้อมูลสินค้าสำหรับ autocomplete (ครั้งเดียวตอน init)"""
        try:
            self.db.connect()
            products = self.db.fetch_all("""
                SELECT product_id, product_name, barcode, retail_price, stock_quantity
                FROM products 
                WHERE is_active = 1
                ORDER BY product_name
                LIMIT 500
            """)
            self.db.disconnect()
            
            # เก็บข้อมูลสำหรับ smart search — ชื่อสินค้า + บาร์โค้ด + ราคา + สต็อก
            self._autocomplete_data = []
            for p in products:
                self._autocomplete_data.append({
                    'name': p['product_name'],
                    'barcode': p['barcode'] or '',
                    'price': p['retail_price'],
                    'stock': p['stock_quantity'],
                    'id': p['product_id']
                })
        except Exception as e:
            print(f"[WARN] Failed to load autocomplete data: {e}")
            self._autocomplete_data = []
    
    # ================================================================
    # Smart Search — ระบบค้นหาอัจฉริยะแบบ Dropdown ขณะพิมพ์
    # ================================================================
    
    def _on_search_key_release(self, event):
        """เรียกทุกครั้งที่ปล่อยปุ่มในช่องค้นหา — แสดง suggestion dropdown"""
        # ข้ามปุ่มที่ไม่ใช่ตัวอักษร (ลูกศร, Ctrl, Shift ฯลฯ)
        if event.keysym in ('Return', 'Up', 'Down', 'Escape', 'Shift_L', 'Shift_R',
                            'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Tab',
                            'Caps_Lock', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6',
                            'F7', 'F8', 'F9', 'F10', 'F11', 'F12'):
            return
        
        # Debounce — รอ 150ms หลังพิมพ์ตัวสุดท้ายก่อนค้นหา (ลด CPU)
        if self._suggestion_debounce_id:
            self.after_cancel(self._suggestion_debounce_id)
        self._suggestion_debounce_id = self.after(150, self._update_suggestions)
    
    def _update_suggestions(self):
        """อัปเดตรายการแนะนำจากข้อมูลที่พิมพ์"""
        query = self.search_entry.get().strip().lower()
        query = translate_thai_barcode(query)  # แปลง barcode ภาษาไทยอัตโนมัติ
        
        if not query or len(query) < 1:
            self._hide_suggestions()
            return
        
        # ค้นหาจากข้อมูล cache ในหน่วยความจำ (ไม่ query DB = เร็วมาก)
        matches = []
        query_lower = query.lower()
        for item in self._autocomplete_data:
            name_lower = item['name'].lower()
            barcode_lower = item['barcode'].lower()
            
            # ตรวจหาคำที่ตรงหรือใกล้เคียง
            if query_lower in name_lower or query_lower in barcode_lower:
                matches.append(item)
            elif len(query_lower) >= 2:
                # Fuzzy match: ตรวจสอบว่าตัวอักษรทุกตัวอยู่ในชื่อตามลำดับ
                idx = 0
                for char in query_lower:
                    pos = name_lower.find(char, idx)
                    if pos == -1:
                        break
                    idx = pos + 1
                else:
                    matches.append(item)
            
            if len(matches) >= 8:  # จำกัดแสดง 8 รายการ
                break
        
        if matches:
            self._show_suggestions(matches)
        else:
            self._hide_suggestions()
    
    def _show_suggestions(self, matches):
        """แสดง dropdown รายการแนะนำ"""
        self._hide_suggestions()  # ล้างเดิม
        
        # สร้าง frame สำหรับ dropdown
        self._suggestion_frame = tk.Toplevel(self.winfo_toplevel())
        self._suggestion_frame.withdraw()  # ซ่อนไว้ก่อนจนกว่าจะจัดตำแหน่งเสร็จ
        self._suggestion_frame.overrideredirect(True)  # ไม่มี title bar
        self._suggestion_frame.attributes('-topmost', True)
        
        # คำนวณตำแหน่ง dropdown ให้อยู่ใต้ช่องค้นหา
        self.search_entry.update_idletasks()
        x = self.search_entry.winfo_rootx()
        y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height()
        w = self.search_entry.winfo_width() + 100  # กว้างกว่าช่อง search เล็กน้อย
        
        # Container frame พร้อมเงาและขอบมน
        container = tk.Frame(self._suggestion_frame, bg='#E0E0E0', padx=1, pady=1)
        container.pack(fill='both', expand=True)
        
        inner = tk.Frame(container, bg='white')
        inner.pack(fill='both', expand=True)
        
        self._suggestion_items = []  # เก็บ reference ของแต่ละแถว
        self._suggestion_selected = -1  # index ที่เลือก
        self._suggestion_matches = matches  # เก็บข้อมูลที่ค้นพบ
        
        for i, item in enumerate(matches):
            row = tk.Frame(inner, bg='white', cursor='hand2')
            row.pack(fill='x', padx=2, pady=1)
            
            # ชื่อสินค้า (ซ้าย)
            name_text = item['name']
            if len(name_text) > 35:
                name_text = name_text[:35] + '...'
            
            name_lbl = tk.Label(
                row, text=name_text,
                font=('Sarabun', 14),
                bg='white', fg='#212121',
                anchor='w', padx=10, pady=6
            )
            name_lbl.pack(side='left', fill='x', expand=True)
            
            # ราคาและสต็อก (ขวา)
            price_text = f"฿{item['price']:,.0f}"
            stock_text = f"คงเหลือ {item['stock']}"
            stock_color = '#4CAF50' if item['stock'] > 5 else '#F44336'
            
            info_frame = tk.Frame(row, bg='white')
            info_frame.pack(side='right', padx=10)
            
            tk.Label(
                info_frame, text=price_text,
                font=('Sarabun', 13, 'bold'),
                bg='white', fg=COLORS['primary']
            ).pack(side='left', padx=(0, 8))
            
            tk.Label(
                info_frame, text=stock_text,
                font=('Sarabun', 11),
                bg='white', fg=stock_color
            ).pack(side='left')
            
            # Separator line
            if i < len(matches) - 1:
                tk.Frame(inner, bg='#EEEEEE', height=1).pack(fill='x', padx=8)
            
            # Bind events — ทำให้ทั้งแถวและ label ทุกตัวคลิกได้
            for widget in [row, name_lbl, info_frame]:
                widget.bind('<Button-1>', lambda e, idx=i: self._select_suggestion(idx))
                widget.bind('<Enter>', lambda e, r=row, idx=i: self._highlight_suggestion(idx))
                widget.bind('<Leave>', lambda e, r=row, idx=i: self._unhighlight_suggestion(idx))
            
            self._suggestion_items.append(row)
        
        # จัดตำแหน่งและแสดง
        self._suggestion_frame.geometry(f"{w}x{len(matches) * 42 + 4}+{x}+{y}")
        self._suggestion_frame.deiconify()
        self._suggestion_visible = True
        
        # ปิด dropdown เมื่อคลิกข้างนอก
        self.winfo_toplevel().bind('<Button-1>', self._on_click_outside, add='+')
    
    def _hide_suggestions(self, event=None):
        """ซ่อน dropdown"""
        if self._suggestion_frame and self._suggestion_frame.winfo_exists():
            self._suggestion_frame.destroy()
        self._suggestion_frame = None
        self._suggestion_visible = False
        self._suggestion_selected = -1
        try:
            self.winfo_toplevel().unbind('<Button-1>')
        except Exception:
            pass
    
    def _highlight_suggestion(self, index):
        """ไฮไลท์แถว"""
        if 0 <= index < len(self._suggestion_items):
            row = self._suggestion_items[index]
            for widget in row.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(bg='#E3F2FD')
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg='#E3F2FD')
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label):
                            child.configure(bg='#E3F2FD')
            row.configure(bg='#E3F2FD')
            self._suggestion_selected = index
    
    def _unhighlight_suggestion(self, index):
        """ยกเลิกไฮไลท์"""
        if 0 <= index < len(self._suggestion_items):
            row = self._suggestion_items[index]
            for widget in row.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(bg='white')
                elif isinstance(widget, tk.Frame):
                    widget.configure(bg='white')
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label):
                            child.configure(bg='white')
            row.configure(bg='white')
    
    def _suggestion_navigate(self, event):
        """เลื่อนขึ้น/ลงในรายการแนะนำด้วยปุ่มลูกศร"""
        if not self._suggestion_visible or not self._suggestion_items:
            return
        
        # ยกเลิก highlight เดิม
        if self._suggestion_selected >= 0:
            self._unhighlight_suggestion(self._suggestion_selected)
        
        if event.keysym == 'Down':
            self._suggestion_selected = min(
                self._suggestion_selected + 1, len(self._suggestion_items) - 1
            )
        elif event.keysym == 'Up':
            self._suggestion_selected = max(self._suggestion_selected - 1, 0)
        
        self._highlight_suggestion(self._suggestion_selected)
        return 'break'  # ป้องกัน cursor กระโดดในช่อง search
    
    def _select_suggestion(self, index):
        """เลือกรายการจาก dropdown → เพิ่มสินค้าเข้าตะกร้าทันที"""
        if 0 <= index < len(self._suggestion_matches):
            item = self._suggestion_matches[index]
            self._hide_suggestions()
            
            # ใส่ชื่อสินค้าลงช่อง search แล้วกด search
            self.search_entry.delete(0, 'end')
            self.search_entry.insert(0, item['barcode'] if item['barcode'] else item['name'])
            self.search_product()
    
    def _on_search_enter(self, event=None):
        """กด Enter ในช่องค้นหา — ถ้ามี suggestion ที่เลือกอยู่ ให้ใช้ตัวนั้น"""
        if self._suggestion_visible and self._suggestion_selected >= 0:
            self._select_suggestion(self._suggestion_selected)
            return 'break'
        else:
            self._hide_suggestions()
            self.search_product()
    
    def _on_click_outside(self, event):
        """คลิกข้างนอก dropdown → ซ่อน"""
        if self._suggestion_frame and self._suggestion_frame.winfo_exists():
            # ตรวจสอบว่าคลิกข้างนอก dropdown จริงหรือไม่
            try:
                widget = event.widget
                if str(widget).startswith(str(self._suggestion_frame)):
                    return  # คลิกใน dropdown → ไม่ซ่อน
            except Exception:
                pass
            self._hide_suggestions()
    
    def setup_keyboard_shortcuts(self):
        """ตั้งค่า keyboard shortcuts"""
        # Global Binding - ผูกกับหน้าต่างหลักโดยตรง (Hardtest)
        parent_window = self.winfo_toplevel()
        
        # F1: Focus ช่องค้นหา
        parent_window.bind("<F1>", lambda e: self.search_entry.focus())
        
        # F10: ชำระเงิน (จำเป็นต่อการใช้งาน)
        # ตรวจสอบว่าหน้าต่างยังเปิดอยู่และมีสินค้าในตะกร้า
        def on_f10(event):
            if self.winfo_exists() and self.cart_items:
                self.show_checkout_dialog()
            return "break" # ป้องกัน event propagation
            
        parent_window.bind("<F10>", on_f10)
        
        # F11: ยกเลิกการขาย (ล้างตะกร้า)
        def on_f11(event):
            if self.winfo_exists():
                self.clear_cart()
            return "break"
        parent_window.bind("<F11>", on_f11)

        # F9: ขึ้นหน้าการขายใหม่ (New Session)
        def on_f9(event):
            if self.winfo_exists():
                self.add_new_session()
            return "break"
        parent_window.bind("<F9>", on_f9)

        # F7: เปิดหน้าพิมพ์ส่วนลด (Focus ช่องส่วนลด)
        def on_f7(event):
            if self.winfo_exists() and hasattr(self, 'discount_entry'):
                self.discount_entry.focus()
                self.discount_entry.select_range(0, 'end')
            return "break"
        parent_window.bind("<F7>", on_f7)

        # F8: เปิด/ปิด VAT และกรอกเปอร์เซ็นต์
        def on_f8(event):
            if self.winfo_exists() and hasattr(self, 'vat_checkbox'):
                # Toggle checkbox
                if self.vat_checkbox.get():
                    self.vat_checkbox.deselect()
                else:
                    self.vat_checkbox.select()
                self.toggle_vat()
                
                # Focus ช่องกรอก VAT
                self.vat_entry.focus()
                self.vat_entry.select_range(0, 'end')
            return "break"
        parent_window.bind("<F8>", on_f8)
        
        # F12: ลบหน้าการขายปัจจุบัน (Close Current Session)
        def on_f12(event):
            if self.winfo_exists():
                self.remove_session(self.active_session_index)
            return "break"
        parent_window.bind("<F12>", on_f12)
        
        # Also bind entries to prevent default behavior if needed
        for entry in [self.search_entry]:
            entry.bind("<F10>", on_f10)
            entry.bind("<F11>", on_f11)
            entry.bind("<F9>", on_f9)
            entry.bind("<F7>", on_f7)
            entry.bind("<F8>", on_f8)
            entry.bind("<F12>", on_f12)
            
        # ทำให้ frame focus ได้
        self.focus_set()
    
    def remove_last_item(self):
        """ลบรายการล่าสุดในตะกร้า (Shortcut: Ctrl+Q)"""
        if self.cart_items:
            removed = self.cart_items.pop()
            self.update_cart_display()
            self.update_summary()
            self.update_customer_display()  # อัพเดทจอลูกค้า
            print(f"ลบ: {removed['product_name']}")
    
    def toggle_customer_display(self):
        """เปิด/ปิดจอแสดงผลลูกค้า"""
        try:
            from ui.customer_display import CustomerDisplayWindow
            
            if not hasattr(self.root_window, 'customer_display') or self.root_window.customer_display is None or not self.root_window.customer_display.winfo_exists():
                # เปิดจอลูกค้า โดยใช้ root_window เพื่อให้ไม่ถูกทำลายเมื่อเปลี่ยนหน้า
                self.root_window.customer_display = CustomerDisplayWindow(self.root_window)
                self.customer_display = self.root_window.customer_display
                self.display_btn.configure(
                    text="📺 ปิดจอลูกค้า",
                    fg_color=COLORS["danger"]
                )
                self.update_customer_display()
            else:
                # ปิดจอลูกค้า
                self.root_window.customer_display.destroy()
                self.root_window.customer_display = None
                self.customer_display = None
                self.display_btn.configure(
                    text="📺 เปิดจอลูกค้า",
                    fg_color=COLORS["info"]
                )
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดจอลูกค้าได้: {e}")
    
    def update_customer_display(self, paid=0, change=0):
        """อัพเดทข้อมูลบนจอลูกค้า (Real-time)"""
        if self.customer_display and self.customer_display.winfo_exists():
            try:
                # เตรียมข้อมูลรายการสินค้า
                cart_items = []
                for item in self.cart_items:
                    cart_items.append({
                        "name": item['product_name'],
                        "quantity": item['quantity'],
                        "price": item['unit_price'],
                        "total": item['total'],
                        "image_path": item.get('image_path') # item is a standard dict here, .get() is fine
                    })
                
                # คำนวณยอดรวมตาม VAT settings
                subtotal = sum(item['total'] for item in self.cart_items)
                
                # ส่วนลด
                try:
                    discount_value = float(self.discount_entry.get())
                except:
                    discount_value = 0
                
                discount_type = self.discount_type_combo.get()
                if discount_type == "%":
                    discount_amount = (subtotal * discount_value) / 100
                else:
                    discount_amount = discount_value
                
                after_discount = subtotal - discount_amount
                if after_discount < 0:
                    after_discount = 0
                
                # VAT
                if self.vat_enabled:
                    tax_amount = after_discount * self.vat_rate
                else:
                    tax_amount = 0
                
                total = after_discount + tax_amount
                
                # สร้าง QR Code (PromptPay)
                qr_data = f"PromptPay:0812345678:Amount:{total:.2f}"
                
                # อัพเดทจอแบบ Real-time
                self.customer_display.update_display(cart_items, total, qr_data, paid=paid, change=change)
            except Exception as e:
                print(f"Error updating customer display: {e}")
    
    def toggle_vat(self):
        """เปิด/ปิด VAT"""
        self.vat_enabled = self.vat_checkbox.get()
        
        # อัพเดท label
        if self.vat_enabled:
            self.vat_label_text.configure(text=f"ภาษี VAT")
        else:
            self.vat_label_text.configure(text=f"ภาษี VAT (ปิด)")
        
        # คำนวณใหม่
        self.update_summary()
        self.update_customer_display()  # อัพเดทจอลูกค้า
    
    def update_vat_rate(self):
        """อัพเดทอัตรา VAT จากช่องกรอก"""
        try:
            vat_percent = float(self.vat_entry.get())
            if 0 <= vat_percent <= 100:
                self.vat_rate = vat_percent / 100
                self.vat_label_text.configure(text=f"ภาษี VAT")
                self.update_summary()
                self.update_customer_display()  # อัพเดทจอลูกค้า
            else:
                # ถ้าเกิน 100 ให้รีเซ็ต
                self.vat_entry.delete(0, 'end')
                self.vat_entry.insert(0, str(int(self.vat_rate * 100)))
        except Exception:
            # ถ้ากรอกไม่ใช่ตัวเลข
            pass
