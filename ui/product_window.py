# -*- coding: utf-8 -*-
"""
หน้าจัดการสินค้า
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
from utils import (
    generate_product_barcode, create_barcode, optimize_image, 
    ExcelManager, bind_english_input, create_barcode_labels_pdf
)
from config import *
from database import DatabaseManager
import os
import pandas as pd
from pathlib import Path
from datetime import datetime


class ProductManagementFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการสินค้า - Optimized with caching"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        self.current_product_id = None
        self.selected_image_path = None
        self.last_category = None # จำหมวดหมู่ล่าสุดที่เลือก
        
        # Performance optimization
        self._categories_cache = None  # Cache หมวดหมู่
        self._products_cache = []  # Cache สินค้าทั้งหมด
        self._image_cache = {}  # Cache รูปภาพที่โหลดแล้ว
        self._last_search = ""  # เก็บคำค้นหาล่าเสุด
        self._search_timer = None  # Debounce timer for search (BUG-016)
        
        # Pagination for performance
        self._current_page = 1
        self._items_per_page = PERFORMANCE_MODE["items_per_page"] if PERFORMANCE_MODE["enabled"] else 100
        self._total_products = 0
        
        self.create_widgets()
        self.load_categories_cache()  # โหลดหมวดหมู่ครั้งเดียว
        self.load_products()
        self.setup_keyboard_shortcuts()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text="📦 จัดการสินค้า",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(side="left")
        
        # ปุ่มด้านขวา
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 รีเฟรช",
            font=FONTS["button"],
            width=120,
            height=40,
            fg_color=COLORS["info"],
            hover_color=COLORS["hover"],
            command=self.load_products
        )
        refresh_btn.pack(side="left", padx=5)
        
        add_btn = ctk.CTkButton(
            btn_frame,
            text="➕ เพิ่มสินค้า",
            font=FONTS["button"],
            width=120,
            height=40,
            fg_color=COLORS["success"],
            hover_color="#45a049",
            command=self.show_add_product_dialog
        )
        add_btn.pack(side="left", padx=5)

        import_btn = ctk.CTkButton(
            btn_frame,
            text="📤 นำเข้า Excel",
            font=FONTS["button"],
            width=120,
            height=40,
            fg_color=COLORS["primary"],
            command=self.import_products_action
        )
        import_btn.pack(side="left", padx=5)

        template_btn = ctk.CTkButton(
            btn_frame,
            text="📥 เทมเพลต",
            font=FONTS["button"],
            width=110,
            height=40,
            fg_color=COLORS["text_light"],
            command=self.download_template_action
        )
        template_btn.pack(side="left", padx=5)
        
        barcode_print_btn = ctk.CTkButton(
            btn_frame,
            text="🖨️ พิมพ์บาร์โค้ด",
            font=FONTS["button"],
            width=135,
            height=40,
            fg_color="#8e44ad",
            hover_color="#732d91",
            command=self.show_barcode_print_dialog
        )
        barcode_print_btn.pack(side="left", padx=5)
        
        # กรอบหลัก
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # ช่องค้นหา
        search_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 15))
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="🔍 ค้นหา:",
            font=FONTS["body"],
            text_color=COLORS["text_dark"]
        )
        search_label.pack(side="left", padx=20, pady=15)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="ค้นหาด้วยบาร์โค้ด, ชื่อสินค้า หรือหมวดหมู่...",
            font=FONTS["body"],
            height=40,
            width=400
        )
        self.search_entry.pack(side="left", padx=(0, 20), pady=15)
        self.search_entry.bind("<KeyRelease>", lambda e: self._debounce_search())
        
        # ตารางสินค้า
        table_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True)
        
        # Header ตาราง
        header_frame = ctk.CTkFrame(table_frame, fg_color=COLORS["primary"], corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        headers = [
            ("รูป", 80),
            ("บาร์โค้ด", 120),
            ("ชื่อสินค้า", 250),
            ("หมวดหมู่", 150),
            ("ราคาขาย", 100),
            ("สต็อก", 80),
            ("สถานะ", 80),
            ("จัดการ", 150)
        ]
        
        for header, width in headers:
            label = ctk.CTkLabel(
                header_frame,
                text=header,
                font=FONTS["button"],
                text_color="white",
                width=width
            )
            label.pack(side="left", padx=5, pady=10)
        
        # Scrollable frame สำหรับรายการสินค้า
        self.products_container = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="white",
            corner_radius=0
        )
        self.products_container.pack(fill="both", expand=True, padx=0, pady=0)
        
    def load_products(self, page=1):
        """โหลดรายการสินค้า (with Pagination)"""
        self._current_page = page
        offset = (page - 1) * self._items_per_page
        
        # ล้างรายการเดิม
        for widget in self.products_container.winfo_children():
            widget.destroy()
        
        # นับจำนวนทั้งหมด
        self.db.connect()
        count_result = self.db.fetch_one("""
            SELECT COUNT(*) as total FROM products WHERE is_active = 1
        """)
        self._total_products = count_result['total'] if count_result else 0
        
        # ดึงข้อมูลจากฐานข้อมูล (with LIMIT and OFFSET)
        products = self.db.fetch_all("""
            SELECT p.*, c.category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1
            ORDER BY p.product_id DESC
            LIMIT ? OFFSET ?
        """, (self._items_per_page, offset))
        self.db.disconnect()
        
        if not products:
            no_data_label = ctk.CTkLabel(
                self.products_container,
                text="ไม่มีข้อมูลสินค้า\nคลิกปุ่ม 'เพิ่มสินค้า' เพื่อเพิ่มสินค้าใหม่",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            )
            no_data_label.pack(pady=50)
            return
        
        # แสดงรายการสินค้า
        for idx, product in enumerate(products):
            self.create_product_row(product, idx)
        
        # เพิ่ม Pagination controls
        if PERFORMANCE_MODE["enabled"] and PERFORMANCE_MODE["pagination_enabled"]:
            self.create_pagination_controls()
    
    def create_product_row(self, product, index):
        """สร้างแถวสินค้า"""
        bg_color = COLORS["light"] if index % 2 == 0 else "white"
        
        row_frame = ctk.CTkFrame(
            self.products_container,
            fg_color=bg_color,
            corner_radius=0,
            height=80
        )
        row_frame.pack(fill="x", padx=0, pady=1)
        row_frame.pack_propagate(False)
        
        # รูปภาพ
        img_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=80)
        img_frame.pack(side="left", padx=5, pady=5)
        img_frame.pack_propagate(False)
        
        try:
            if product['image_path'] and os.path.exists(product['image_path']):
                # เช็ค cache ก่อน
                cache_key = f"{product['product_id']}_{product['image_path']}"
                if cache_key in self._image_cache:
                    photo = self._image_cache[cache_key]
                    img_label = ctk.CTkLabel(img_frame, image=photo, text="")
                    img_label.image = photo
                    img_label.pack()
                else:
                    # โหลดและบีบอัดรูปภาพ
                    img = Image.open(product['image_path'])
                    
                    # ใช้ Performance Mode Settings
                    if PERFORMANCE_MODE["enabled"] and PERFORMANCE_MODE["compress_images"]:
                        # ใช้ BILINEAR แทน LANCZOS (เร็วกว่า)
                        thumb_size = IMAGE_OPTIMIZATION["thumbnail_size"]
                        resample = Image.Resampling.BILINEAR if IMAGE_OPTIMIZATION["resample_method"] == "BILINEAR" else Image.Resampling.LANCZOS
                        img = img.resize(thumb_size, resample)
                    else:
                        img = img.resize((60, 60), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    
                    # เก็บลง cache (จำกัดจำนวน)
                    max_cache = PERFORMANCE_MODE["max_cached_images"] if PERFORMANCE_MODE["enabled"] else 50
                    try:
                        import performance_config
                        max_cache = performance_config.MAX_IMAGE_CACHE_SIZE
                    except ImportError:
                        pass
                    if len(self._image_cache) >= max_cache:
                        # ลบรูปแรกสุด
                        self._image_cache.pop(next(iter(self._image_cache)))
                    self._image_cache[cache_key] = photo
                    
                    img_label = ctk.CTkLabel(img_frame, image=photo, text="")
                    img_label.image = photo
                    img_label.pack()
            else:
                img_label = ctk.CTkLabel(
                    img_frame,
                    text="📦",
                    font=("Arial", 30),
                    text_color=COLORS["text_light"]
                )
                img_label.pack()
        except:
            img_label = ctk.CTkLabel(
                img_frame,
                text="📦",
                font=("Arial", 30),
                text_color=COLORS["text_light"]
            )
            img_label.pack()
        
        # บาร์โค้ด
        barcode_label = ctk.CTkLabel(
            row_frame,
            text=product['barcode'] or '-',
            font=FONTS["body"],
            width=120,
            anchor="w"
        )
        barcode_label.pack(side="left", padx=5)
        
        # ชื่อสินค้า
        name_label = ctk.CTkLabel(
            row_frame,
            text=product['product_name'],
            font=FONTS["body"],
            width=250,
            anchor="w"
        )
        name_label.pack(side="left", padx=5)
        
        # หมวดหมู่
        category_label = ctk.CTkLabel(
            row_frame,
            text=product['category_name'] or '-',
            font=FONTS["body"],
            width=150,
            anchor="w"
        )
        category_label.pack(side="left", padx=5)
        
        # ราคา
        price_label = ctk.CTkLabel(
            row_frame,
            text=f"฿{product['retail_price']:,.2f}",
            font=FONTS["body"],
            width=100,
            anchor="e"
        )
        price_label.pack(side="left", padx=5)
        
        # สต็อก
        stock_color = COLORS["danger"] if product['stock_quantity'] <= product['min_stock'] else COLORS["text_dark"]
        stock_label = ctk.CTkLabel(
            row_frame,
            text=str(product['stock_quantity']),
            font=FONTS["body"],
            width=80,
            text_color=stock_color,
            anchor="center"
        )
        stock_label.pack(side="left", padx=5)
        
        # สถานะ
        status_text = "✓" if product['is_active'] else "✗"
        status_color = COLORS["success"] if product['is_active'] else COLORS["danger"]
        status_label = ctk.CTkLabel(
            row_frame,
            text=status_text,
            font=("Arial", 20, "bold"),
            width=80,
            text_color=status_color,
            anchor="center"
        )
        status_label.pack(side="left", padx=5)
        
        # ปุ่มจัดการ
        btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=150)
        btn_frame.pack(side="left", padx=5)
        btn_frame.pack_propagate(False)
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["info"],
            hover_color=COLORS["hover"],
            command=lambda p=product: self.show_edit_product_dialog(p)
        )
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["danger"],
            hover_color="#cc0000",
            command=lambda p=product: self.delete_product(p['product_id'])
        )
        delete_btn.pack(side="left", padx=2)
        
    def _debounce_search(self):
        """Debounce search — รอดีเลย์ตามที่ตั้งค่าใน config หลังพิมพ์เสร็จค่อย query"""
        if self._search_timer:
            self.after_cancel(self._search_timer)
        ms = 300
        try:
            import performance_config
            ms = performance_config.DEBOUNCE_SEARCH_MS
        except ImportError:
            pass
        self._search_timer = self.after(ms, self.search_products)
    
    def search_products(self):
        """ค้นหาสินค้า"""
        search_text = self.search_entry.get().strip().lower()
        
        if not search_text:
            self.load_products()
            return
        
        # ล้างรายการเดิม
        for widget in self.products_container.winfo_children():
            widget.destroy()
        
        # ค้นหาจากฐานข้อมูล
        self.db.connect()
        products = self.db.fetch_all("""
            SELECT p.*, c.category_name 
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1 
            AND (LOWER(p.product_name) LIKE ? 
                 OR LOWER(p.barcode) LIKE ? 
                 OR LOWER(c.category_name) LIKE ?)
            ORDER BY p.product_id DESC
        """, (f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"))
        self.db.disconnect()
        
        if not products:
            no_data_label = ctk.CTkLabel(
                self.products_container,
                text=f"ไม่พบสินค้าที่ค้นหา: '{search_text}'",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            )
            no_data_label.pack(pady=50)
            return
        
        # แสดงผลลัพธ์
        for idx, product in enumerate(products):
            self.create_product_row(product, idx)
    
    # ================================================================
    #  Wizard เพิ่มสินค้าแบบ Step-by-Step
    #  Flow: บาร์โค้ด > ชื่อสินค้า > ราคาทุน > ราคาขาย > หมวดหมู่
    #  บันทึกลง DB อัตโนมัติหลังเลือกหมวดหมู่
    # ================================================================

    def show_add_product_dialog(self):
        """เปิด Wizard เพิ่มสินค้าทีละขั้น — เร็วกว่าฟอร์มเดิม"""
        self.current_product_id = None
        self.selected_image_path = None

        # เก็บข้อมูลที่กรอกจากแต่ละ step
        self._wizard_data = {
            "barcode": "",
            "name": "",
            "cost": "0",
            "price": "0",
            "stock": "0",
            "category": "",
        }

        # เริ่ม step แรก
        self._wizard_step_barcode()

    # ---------- ตัวช่วยสร้างหน้าต่าง Wizard ----------

    def _wizard_create_dialog(self, title_text, step_label):
        """สร้างหน้าต่าง dialog กลางสำหรับทุก step
        
        Returns:
            tuple: (dialog, content_frame) — ใส่ widget ใน content_frame
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title("เพิ่มสินค้าใหม่")
        dialog.geometry("500x320")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)

        # จัดกลางจอ
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 160
        dialog.geometry(f"+{x}+{y}")

        # กรอบหลัก
        main = ctk.CTkFrame(dialog, fg_color=COLORS["light"])
        main.pack(fill="both", expand=True)

        # แถบ step ด้านบน
        step_bar = ctk.CTkLabel(
            main, text=step_label,
            font=("Sarabun", 13),
            text_color=COLORS["text_light"],
            fg_color="white", corner_radius=8, height=30
        )
        step_bar.pack(fill="x", padx=20, pady=(15, 5))

        # หัวข้อ
        ctk.CTkLabel(
            main, text=title_text,
            font=("Sarabun", 22, "bold"),
            text_color=COLORS["primary"]
        ).pack(pady=(10, 15))

        # กรอบเนื้อหา
        content = ctk.CTkFrame(main, fg_color="white", corner_radius=12)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        return dialog, content

    # ---------- Step 1: บาร์โค้ด ----------

    def _wizard_step_barcode(self):
        """Step 1 — สแกนหรือพิมพ์บาร์โค้ด"""
        dialog, content = self._wizard_create_dialog(
            "สแกนหรือพิมพ์บาร์โค้ด",
            "ขั้นตอน 1/6 — บาร์โค้ด"
        )

        # ช่องกรอก
        entry = ctk.CTkEntry(
            content, font=("Sarabun", 20), height=50,
            placeholder_text="สแกนบาร์โค้ดหรือพิมพ์ที่นี่..."
        )
        entry.pack(fill="x", padx=30, pady=(30, 10))

        # บังคับ EN input สำหรับปืนบาร์โค้ดทุกรุ่น
        bind_english_input(entry)

        # ปุ่มสร้างอัตโนมัติ
        def auto_gen():
            entry.delete(0, "end")
            entry.insert(0, generate_product_barcode())

        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkButton(
            btn_frame, text="สร้างอัตโนมัติ",
            font=("Sarabun", 14), width=140, height=38,
            fg_color=COLORS["secondary"], command=auto_gen
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="ข้ามขั้นตอนนี้",
            font=("Sarabun", 14), width=120, height=38,
            fg_color=COLORS["text_light"],
            command=lambda: go_next("")
        ).pack(side="right")

        # กดไปขั้นตอนถัดไป
        def go_next(override_val=None):
            val = override_val if override_val is not None else entry.get().strip()
            self._wizard_data["barcode"] = val
            dialog.destroy()
            self._wizard_step_name()

        entry.bind("<Return>", lambda e: go_next())

        # Auto-focus ที่ช่องกรอก
        dialog.after(100, entry.focus_set)

    # ---------- Step 2: ชื่อสินค้า ----------

    def _wizard_step_name(self):
        """Step 2 — กรอกชื่อสินค้า (จำเป็น)"""
        dialog, content = self._wizard_create_dialog(
            "ชื่อสินค้า",
            "ขั้นตอน 2/6 — ชื่อสินค้า"
        )

        entry = ctk.CTkEntry(
            content, font=("Sarabun", 20), height=50,
            placeholder_text="พิมพ์ชื่อสินค้า..."
        )
        entry.pack(fill="x", padx=30, pady=(40, 15))

        err_label = ctk.CTkLabel(
            content, text="", font=("Sarabun", 13),
            text_color=COLORS["danger"]
        )
        err_label.pack(padx=30)

        def go_next(event=None):
            val = entry.get().strip()
            if not val:
                err_label.configure(text="กรุณากรอกชื่อสินค้า")
                return
            self._wizard_data["name"] = val
            dialog.destroy()
            self._wizard_step_cost()

        entry.bind("<Return>", go_next)

        dialog.after(100, entry.focus_set)

    # ---------- Step 3: ราคาทุน ----------

    def _wizard_step_cost(self):
        """Step 3 — ราคาทุน (ไม่บังคับ)"""
        dialog, content = self._wizard_create_dialog(
            "ราคาทุน (บาท)",
            "ขั้นตอน 3/6 — ราคาทุน"
        )

        entry = ctk.CTkEntry(
            content, font=("Sarabun", 20), height=50,
            placeholder_text="0.00"
        )
        entry.pack(fill="x", padx=30, pady=(40, 15))

        def go_next(event=None):
            val = entry.get().strip() or "0"
            try:
                float(val)
            except ValueError:
                return  # ป้องกัน input ผิด
            self._wizard_data["cost"] = val
            dialog.destroy()
            self._wizard_step_price()

        entry.bind("<Return>", go_next)

        dialog.after(100, entry.focus_set)

    # ---------- Step 4: ราคาขาย ----------

    def _wizard_step_price(self):
        """Step 4 — ราคาขายปลีก (จำเป็น)"""
        dialog, content = self._wizard_create_dialog(
            "ราคาขาย (บาท)",
            "ขั้นตอน 4/6 — ราคาขาย"
        )

        entry = ctk.CTkEntry(
            content, font=("Sarabun", 20), height=50,
            placeholder_text="0.00"
        )
        entry.pack(fill="x", padx=30, pady=(40, 15))

        def go_next(event=None):
            val = entry.get().strip() or "0"
            try:
                float(val)
            except ValueError:
                return
            self._wizard_data["price"] = val
            dialog.destroy()
            self._wizard_step_stock()

        entry.bind("<Return>", go_next)

        dialog.after(100, entry.focus_set)

    # ---------- Step 5: จำนวนสต็อกเริ่มต้น ----------

    def _wizard_step_stock(self):
        """Step 5 — จำนวนสต็อกเริ่มต้น"""
        dialog, content = self._wizard_create_dialog(
            "จำนวนสต็อกเริ่มต้น",
            "ขั้นตอน 5/6 — จำนวนสต็อก"
        )

        entry = ctk.CTkEntry(
            content, font=("Sarabun", 20), height=50,
            placeholder_text="0"
        )
        entry.pack(fill="x", padx=30, pady=(40, 15))
        entry.insert(0, "0")

        def go_next(event=None):
            val = entry.get().strip() or "0"
            try:
                int(val)
            except ValueError:
                return
            self._wizard_data["stock"] = val
            dialog.destroy()
            self._wizard_step_category()

        entry.bind("<Return>", go_next)

        dialog.after(100, entry.focus_set)

    # ---------- Step 6: เลือกหมวดหมู่ ----------

    def _wizard_step_category(self):
        """Step 6 — เลือกหมวดหมู่ด้วยปุ่มหรือกดคีย์ 1/2 แล้วบันทึกทันที"""
        dialog, content = self._wizard_create_dialog(
            "เลือกหมวดหมู่",
            "ขั้นตอน 6/6 — หมวดหมู่  (กด 1 หรือ 2)"
        )

        # สร้างปุ่มสองหมวดหมู่
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(expand=True, pady=20)

        def pick_and_save(cat_name):
            """เลือกหมวดแล้วบันทึกสินค้าลง DB ทันที"""
            self._wizard_data["category"] = cat_name
            dialog.destroy()
            self._wizard_save_to_db()

        ctk.CTkButton(
            btn_frame, text="[1]  สินค้าอุปโภค",
            font=("Sarabun", 20, "bold"),
            width=210, height=70,
            fg_color=COLORS["primary"],
            hover_color=COLORS["secondary"],
            corner_radius=12,
            command=lambda: pick_and_save("สินค้าอุปโภค")
        ).pack(side="left", padx=15)

        ctk.CTkButton(
            btn_frame, text="[2]  สินค้าบริโภค",
            font=("Sarabun", 20, "bold"),
            width=210, height=70,
            fg_color=COLORS["success"],
            hover_color="#45a049",
            corner_radius=12,
            command=lambda: pick_and_save("สินค้าบริโภค")
        ).pack(side="left", padx=15)

        # Keyboard shortcuts: กด 1 = อุปโภค, กด 2 = บริโภค
        dialog.bind("1", lambda e: pick_and_save("สินค้าอุปโภค"))
        dialog.bind("2", lambda e: pick_and_save("สินค้าบริโภค"))
        dialog.focus_set()

    # ---------- บันทึกลง DB ----------

    def _wizard_save_to_db(self):
        """นำข้อมูลจาก wizard ไปบันทึกลงฐานข้อมูลทันที
        
        ใช้ save_product เดิม — ส่งค่า default สำหรับ field ที่ wizard ไม่ได้ถาม
        (หมวดหมู่จะถูกสร้างอัตโนมัติใน save_product ถ้ายังไม่มี)
        """
        data = self._wizard_data

        # เตรียม prices dict ให้ตรงกับ format ของ save_product
        prices = {
            "retail_price": data["price"],
            "wholesale_price": "0",
            "special_price1": "0",
            "special_price2": "0",
        }

        # เรียก save_product เดิม — ส่ง dialog=None เพราะปิดไปแล้ว
        self.save_product(
            dialog=None,
            barcode=data["barcode"],
            name=data["name"],
            category=data["category"],
            cost=data["cost"],
            prices=prices,
            stock=data.get("stock", "0"),
            min_stock="10"
        )
    
    def show_edit_product_dialog(self, product):
        """แสดงหน้าต่างแก้ไขสินค้า"""
        self.current_product_id = product['product_id']
        self.selected_image_path = product['image_path']
        self.show_product_dialog("แก้ไขสินค้า", product)
    
    def show_product_dialog(self, title, product=None):
        """แสดงหน้าต่างฟอร์มสินค้า - REBUILT เพื่อความถูกต้อง 100%"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("750x850") # ปรับขนาดเล็กน้อย
        dialog.transient(self)
        dialog.grab_set()
        
        # ปรับการวางตำแหน่งหนน้าต่างให้อยู่กลางจอ
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (750 // 2)
        y = (dialog.winfo_screenheight() // 2) - (850 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # กรอบหลัก
        main_container = ctk.CTkFrame(dialog, fg_color=COLORS["light"])
        main_container.pack(fill="both", expand=True)
        
        # กรอบหลักแบบ Scrollable
        main_scroll = ctk.CTkScrollableFrame(main_container, fg_color=COLORS["light"])
        main_scroll.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # ฟอนต์ที่ใช้
        label_font = FONTS.get("body", ("Arial", 14))
        entry_font = FONTS.get("body", ("Arial", 14))
        
        # --- Section 1: ข้อมูลหลัก ---
        info_frame = ctk.CTkFrame(main_scroll, fg_color="white", corner_radius=15)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(info_frame, text="📋 ข้อมูลสินค้าหลัก", font=FONTS.get("button", ("Arial", 16, "bold")), text_color=COLORS["primary"]).pack(anchor="w", padx=20, pady=(15, 5))
        
        # บาร์โค้ด
        ctk.CTkLabel(info_frame, text="บาร์โค้ด:", font=label_font).pack(anchor="w", padx=20, pady=(10, 0))
        barcode_inner = ctk.CTkFrame(info_frame, fg_color="transparent")
        barcode_inner.pack(fill="x", padx=20, pady=(0, 10))
        
        barcode_entry = ctk.CTkEntry(barcode_inner, font=entry_font, height=40)
        barcode_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        if product and 'barcode' in product.keys(): 
            barcode_entry.insert(0, product['barcode'] if product['barcode'] else "")
        # บังคับ EN input สำหรับปืนบาร์โค้ดทุกรุ่น
        bind_english_input(barcode_entry)
        
        def auto_barcode():
            barcode_entry.delete(0, 'end')
            barcode_entry.insert(0, generate_product_barcode())
        
        ctk.CTkButton(barcode_inner, text="สร้างอัตโนมัติ", font=label_font, width=120, height=40, fg_color=COLORS["secondary"], command=auto_barcode).pack(side="right")
        
        # ชื่อสินค้า
        ctk.CTkLabel(info_frame, text="ชื่อสินค้า: *", font=label_font).pack(anchor="w", padx=20, pady=(10, 0))
        name_entry = ctk.CTkEntry(info_frame, font=entry_font, height=40, placeholder_text="ระบุชื่อสินค้า")
        name_entry.pack(fill="x", padx=20, pady=(0, 10))
        if product: name_entry.insert(0, product['product_name'])
        
        # หมวดหมู่
        ctk.CTkLabel(info_frame, text="หมวดหมู่:", font=label_font).pack(anchor="w", padx=20, pady=(10, 0))
        self.db.connect()
        cats = self.db.fetch_all("SELECT * FROM categories ORDER BY category_name")
        self.db.disconnect()
        
        cat_names = [c['category_name'] for c in cats]
        cat_combo = ctk.CTkComboBox(info_frame, values=cat_names, font=entry_font, height=40, state="readonly")
        cat_combo.pack(fill="x", padx=20, pady=(0, 20))
        
        if product and 'category_id' in product.keys() and product['category_id']:
            for c in cats:
                if c['category_id'] == product['category_id']:
                    cat_combo.set(c['category_name'])
                    break
        elif self.last_category:
            cat_combo.set(self.last_category)
        elif cat_names:
            cat_combo.set(cat_names[0])

        # --- Section 2: ราคาและสต็อก ---
        price_frame = ctk.CTkFrame(main_scroll, fg_color="white", corner_radius=15)
        price_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(price_frame, text="💰 ราคาและสต็อก", font=FONTS.get("button", ("Arial", 16, "bold")), text_color=COLORS["primary"]).pack(anchor="w", padx=20, pady=(15, 10))
        
        # ราคาทุน และ ราคาขาย (แถวเดียวกัน)
        row1 = ctk.CTkFrame(price_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=5)
        
        # ทุน
        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(col1, text="ราคาทุน:", font=label_font).pack(anchor="w")
        cost_entry = ctk.CTkEntry(col1, font=entry_font, height=40, placeholder_text="0.00")
        cost_entry.pack(fill="x")
        if product: cost_entry.insert(0, str(product['cost_price']))
        
        # ขายปลีก
        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col2, text="ราคาขาย:", font=label_font).pack(anchor="w")
        retail_entry = ctk.CTkEntry(col2, font=entry_font, height=40, placeholder_text="0.00")
        retail_entry.pack(fill="x")
        if product: retail_entry.insert(0, str(product['retail_price']))
        
        # จำนวนสต็อก และ สต็อกขั้นต่ำ (แถวเดียวกัน)
        row2 = ctk.CTkFrame(price_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(10, 20))
        
        # สต็อกปัจจุบัน
        col3 = ctk.CTkFrame(row2, fg_color="transparent")
        col3.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(col3, text="จำนวนสต็อก:", font=label_font).pack(anchor="w")
        stock_entry = ctk.CTkEntry(col3, font=entry_font, height=40, placeholder_text="0", fg_color="white")
        stock_entry.pack(fill="x")
        if product: 
            stock_entry.insert(0, str(product['stock_quantity']))
            ctk.CTkLabel(col3, text="(แก้ไขจำนวนสต็อกใหม่ที่นี่ได้เลย)", font=("Arial", 10), text_color=COLORS["primary"]).pack(anchor="w")
        
        # ขั้นต่ำ
        col4 = ctk.CTkFrame(row2, fg_color="transparent")
        col4.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col4, text="สต็อกขั้นต่ำ:", font=label_font).pack(anchor="w")
        min_stock_entry = ctk.CTkEntry(col4, font=entry_font, height=40, placeholder_text="10")
        min_stock_entry.pack(fill="x")
        if product: min_stock_entry.insert(0, str(product['min_stock']))
        else: min_stock_entry.insert(0, "10")

        # --- Section 3: รูปภาพ ---
        img_frame = ctk.CTkFrame(main_scroll, fg_color="white", corner_radius=15)
        img_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(img_frame, text="📸 รูปภาพสินค้า", font=FONTS.get("button", ("Arial", 16, "bold")), text_color=COLORS["primary"]).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.image_label = ctk.CTkLabel(img_frame, text="📷 คลิกเพื่อเลือกรูปภาพ", font=label_font, text_color=COLORS["text_light"], height=150, fg_color=COLORS["light"], corner_radius=10, cursor="hand2")
        self.image_label.pack(fill="x", padx=20, pady=(5, 20))
        self.image_label.bind("<Button-1>", lambda e: self.select_image())
        
        if product:
            try:
                img_path = product['image_path']
            except (KeyError, IndexError):
                img_path = None
            if img_path and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((150, 150), Image.Resampling.BILINEAR)
                    photo = ImageTk.PhotoImage(img)
                    self.image_label.configure(image=photo, text="")
                    self.image_label.image = photo
                except Exception: pass

        # --- Section 4: ปุ่มดำเนินการ (Sticky - อยู่นอก Scroll) ---
        action_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=0, height=80)
        action_frame.pack(fill="x", side="bottom", padx=0, pady=0)
        action_frame.pack_propagate(False)
        
        # ใส่เส้นแบ่งด้านบนปุ่ม
        ctk.CTkFrame(action_frame, fg_color=COLORS["border"], height=1).pack(fill="x", side="top")
        
        inner_action = ctk.CTkFrame(action_frame, fg_color="transparent")
        inner_action.pack(expand=True, fill="x", padx=20)

        cancel_btn = ctk.CTkButton(inner_action, text="❌ ยกเลิก", font=FONTS.get("button"), width=150, height=45, fg_color=COLORS["danger"], command=dialog.destroy)
        cancel_btn.pack(side="left", padx=10)
        
        def save():
            # เก็บราคาส่ง/ราคาพิเศษจากสินค้าเดิม เพื่อไม่ให้หายเมื่อแก้ไข (BUG-026)
            prices = {'retail_price': retail_entry.get()}
            if product:
                try:
                    prices['wholesale_price'] = str(product['wholesale_price'] or 0)
                except Exception:
                    prices['wholesale_price'] = "0"
                try:
                    prices['special_price1'] = str(product['special_price1'] or 0)
                except Exception:
                    prices['special_price1'] = "0"
                try:
                    prices['special_price2'] = str(product['special_price2'] or 0)
                except Exception:
                    prices['special_price2'] = "0"
            
            self.save_product(
                dialog,
                barcode_entry.get(),
                name_entry.get(),
                cat_combo.get(),
                cost_entry.get(),
                prices,
                stock_entry.get(),
                min_stock_entry.get()
            )
            
        save_btn = ctk.CTkButton(inner_action, text="✅ บันทึกข้อมูล", font=FONTS.get("button"), width=200, height=45, fg_color=COLORS["success"], command=save)
        save_btn.pack(side="right", padx=10)
        
        # --- Bindings ---
        def on_focus_in(event): event.widget.select_range(0, 'end')
        for e in [barcode_entry, name_entry, cost_entry, retail_entry, stock_entry, min_stock_entry]:
            e.bind("<FocusIn>", on_focus_in)
            
        barcode_entry.bind("<Return>", lambda e: name_entry.focus_set())
        name_entry.bind("<Return>", lambda e: retail_entry.focus_set())
        retail_entry.bind("<Return>", lambda e: stock_entry.focus_set())
        stock_entry.bind("<Return>", lambda e: min_stock_entry.focus_set())
        min_stock_entry.bind("<Return>", lambda e: save_btn.focus_set())
        
        # เก็บ reference
        self.product_dialog = dialog
        barcode_entry.focus_set()
        
    def select_image(self):
        """เลือกรูปภาพ"""
        file_path = filedialog.askopenfilename(
            title="เลือกรูปภาพสินค้า",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        
        if file_path:
            try:
                img = Image.open(file_path)
                img = img.resize((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_label.configure(image=photo, text="")
                self.image_label.image = photo
                self.selected_image_path = file_path
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดรูปภาพได้: {e}")
    
    def save_product(self, dialog, barcode, name, category, cost, prices, stock, min_stock):
        """บันทึกสินค้า"""
        # เก็บหมวดหมู่ล่าสุดไว้อัพเดท
        self.last_category = category
        from utils.logger import log_user_action, log_error, log_info
        
        # ตรวจสอบข้อมูล
        if not name.strip():
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกชื่อสินค้า")
            return
        
        try:
            cost_price = float(cost) if cost else 0
            retail_price = float(prices.get('retail_price', 0)) if prices.get('retail_price') else 0
            wholesale_price = float(prices.get('wholesale_price', 0)) if prices.get('wholesale_price') else 0
            special_price1 = float(prices.get('special_price1', 0)) if prices.get('special_price1') else 0
            special_price2 = float(prices.get('special_price2', 0)) if prices.get('special_price2') else 0
            stock_qty = int(stock) if stock else 0
            min_stock_qty = int(min_stock) if min_stock else 10
        except ValueError:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกตัวเลขที่ถูกต้อง")
            return
        
        # หา category_id — ถ้ายังไม่มีในระบบ สร้างอัตโนมัติ
        self.db.connect()
        cat = self.db.fetch_one(
            "SELECT category_id FROM categories WHERE category_name = ?",
            (category,)
        )
        if not cat and category:
            # สร้างหมวดหมู่ใหม่อัตโนมัติ (รองรับ Wizard + Bulk Import)
            self.db.execute(
                "INSERT INTO categories (category_name) VALUES (?)",
                (category,)
            )
            cat = self.db.fetch_one(
                "SELECT category_id FROM categories WHERE category_name = ?",
                (category,)
            )
        category_id = cat['category_id'] if cat else None
        
        # คืนค่าแบรนด์และผู้จัดจำหน่ายเป็น None เพราะยกเลิกฟีเจอร์นี้
        brand_id = None
        vendor_id = None
        
        # จัดการรูปภาพ (ปรับปรุงขนาดอัตโนมัติ)
        image_path = None
        if self.selected_image_path and os.path.exists(self.selected_image_path):
            if "product_" not in os.path.basename(self.selected_image_path):
                # พยายามปรับขนาดและบันทึกไปยังโฟลเดอร์สินค้า
                try:
                    products_dir = PRODUCTS_IMG_DIR
                    products_dir.mkdir(exist_ok=True)
                    
                    # สร้างชื่อไฟล์ใหม่
                    # ใช้นามสกุลจาก config เสมอ (JPEG)
                    ext = ".jpg" if IMAGE_OPTIMIZATION.get("format") == "JPEG" else ".png"
                    filename = f"product_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                    dest_path = products_dir / filename
                    
                    # ใช้ฟังก์ชัน optimize_image
                    success_opt, result_opt = optimize_image(self.selected_image_path, str(dest_path))
                    
                    if success_opt:
                        image_path = result_opt
                    else:
                        # ถ้าล้มเหลว ลอง copy ธรรมดา
                        import shutil
                        dest_path_original = products_dir / f"product_{datetime.now().strftime('%Y%m%d%H%M%S')}{Path(self.selected_image_path).suffix}"
                        shutil.copy2(self.selected_image_path, dest_path_original)
                        image_path = str(dest_path_original)
                except Exception as e:
                    print(f"Error optimizing image: {e}")
                    image_path = self.selected_image_path
            else:
                # ถ้าเป็นรูปในโปรแกรมอยู่แล้ว ให้ปรับปรุงขนาดทับไฟล์เดิม (เผื่อยังไม่ได้ปรับ)
                optimize_image(self.selected_image_path)
                image_path = self.selected_image_path
        
        # บันทึกลงฐานข้อมูล
        self.db.connect()
        
        # --- ตรวจสอบบาร์โค้ดซ้ำ (จัดการกรณีสินค้าเคยลบไปแล้ว) ---
        if not self.current_product_id and barcode:
            existing = self.db.fetch_one(
                "SELECT product_id, is_active FROM products WHERE barcode = ?",
                (barcode,)
            )
            if existing:
                if existing['is_active']:
                    messagebox.showwarning("คำเตือน", f"บาร์โค้ด '{barcode}' นี้มีอยู่ในระบบแล้วและยังใช้งานอยู่")
                    self.db.disconnect()
                    return
                else:
                    # ถ้าเจอแต่สถานะเป็น 0 (เคยลบ) ให้ดึง ID มาใช้เพื่อทำการ UPDATE แทนการ INSERT
                    self.current_product_id = existing['product_id']
                    
        if self.current_product_id:
            # ดึงจำนวนสต็อกเดิมจากฐานข้อมูล เพื่อคำนวณส่วนต่างและทำประวัติออดิต (Audit Trail)
            old_product = self.db.fetch_one(
                "SELECT stock_quantity FROM products WHERE product_id = ?",
                (self.current_product_id,)
            )
            old_stock = old_product['stock_quantity'] if old_product else 0

            # อัพเดทสินค้าเดิม (รวมถึงกรณี Re-activate)
            success = self.db.execute("""
                UPDATE products SET
                    barcode = ?, product_name = ?, category_id = ?,
                    cost_price = ?, retail_price = ?, wholesale_price = ?,
                    special_price1 = ?, special_price2 = ?,
                    stock_quantity = ?, min_stock = ?, image_path = ?,
                    is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE product_id = ?
            """, (barcode, name, category_id, 
                  cost_price, retail_price,
                  wholesale_price, special_price1, special_price2,
                  stock_qty, min_stock_qty, image_path, self.current_product_id))

            # บันทึกประวัติการปรับปรุงสต็อก (ถ้ามีการเปลี่ยนแปลงจำนวน)
            diff = stock_qty - old_stock
            if diff != 0:
                movement_type = 'in' if diff > 0 else 'out'
                self.db.execute("""
                    INSERT INTO stock_movements (
                        product_id, movement_type, quantity,
                        reference_type, user_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.current_product_id, movement_type, abs(diff),
                    'manual_adjustment', self.user_id,
                    f"แก้ไขข้อมูลสินค้า (สต็อกจาก {old_stock} เป็น {stock_qty})"
                ))
        else:
            # เพิ่มใหม่
            success = self.db.execute("""
                INSERT INTO products (
                    barcode, product_name, category_id,
                    cost_price, retail_price, wholesale_price,
                    special_price1, special_price2,
                    stock_quantity, min_stock, image_path, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (barcode, name, category_id,
                  cost_price, retail_price, wholesale_price,
                  special_price1, special_price2,
                  stock_qty, min_stock_qty, image_path))
        
        self.db.disconnect()
        
        if success:
            log_info(f"Product {'updated' if self.current_product_id else 'added'}: {name} (ID: {self.current_product_id or 'New'})")
            messagebox.showinfo("สำเร็จ", MESSAGES["save_success"])
            if dialog:
                dialog.destroy()
            self._categories_cache = None  # Clear cache
            self.load_products()
        else:
            error_msg = self.db.last_error if self.db.last_error else "ไม่ทราบสาเหตุ"
            log_error(f"Failed to save product: {error_msg}")
            messagebox.showerror("ข้อผิดพลาด", f"{MESSAGES['save_failed']}\nสาเหตุ: {error_msg}")
    
    def delete_product(self, product_id):
        """ลบสินค้า"""
        result = messagebox.askyesno(
            "ยืนยันการลบ",
            "คุณต้องการลบสินค้านี้ใช่หรือไม่?\n(จะซ่อนสินค้าไม่ใช่ลบจริง)"
        )
        
        if result:
            self.db.connect()
            success = self.db.execute(
                "UPDATE products SET is_active = 0 WHERE product_id = ?",
                (product_id,)
            )
            self.db.disconnect()
            
            if success:
                messagebox.showinfo("สำเร็จ", "ลบสินค้าเรียบร้อย")
                self.load_products()
    
    def load_categories_cache(self):
        """โหลดหมวดหมู่ทั้งหมดและเก็บใน cache"""
        if self._categories_cache is None:
            self.db.connect()
            categories = self.db.fetch_all("SELECT * FROM categories ORDER BY category_name")
            self.db.disconnect()
            self._categories_cache = categories if categories else []
        return self._categories_cache
    
    def create_pagination_controls(self):
        """สร้างปุ่ม Pagination"""
        total_pages = (self._total_products + self._items_per_page - 1) // self._items_per_page
        
        if total_pages <= 1:
            return
        
        pagination_frame = ctk.CTkFrame(self.products_container, fg_color="transparent")
        pagination_frame.pack(fill="x", pady=10)
        
        # ข้อมูลหน้า
        page_info = ctk.CTkLabel(
            pagination_frame,
            text=f"หน้า {self._current_page} จาก {total_pages} ({self._total_products} รายการ)",
            font=FONTS["body"]
        )
        page_info.pack(side="left", padx=10)
        
        # ปุ่ม
        btn_container = ctk.CTkFrame(pagination_frame, fg_color="transparent")
        btn_container.pack(side="right", padx=10)
        
        # Previous
        if self._current_page > 1:
            prev_btn = ctk.CTkButton(
                btn_container,
                text="◀ ก่อนหน้า",
                width=100,
                command=lambda: self.load_products(self._current_page - 1)
            )
            prev_btn.pack(side="left", padx=2)
        
        # Next
        if self._current_page < total_pages:
            next_btn = ctk.CTkButton(
                btn_container,
                text="ถัดไป ▶",
                width=100,
                command=lambda: self.load_products(self._current_page + 1)
            )
            next_btn.pack(side="left", padx=2)
    
    def download_template_action(self):
        """ดาวน์โหลดเทมเพลต Excel สำหรับนำเข้าสินค้า"""
        try:
            save_path = filedialog.asksaveasfilename(
                title="บันทึกเทมเพลตสินค้า",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"template_สินค้า_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            if not save_path:
                return

            # สร้าง template ด้วย ExcelManager
            columns = [
                "บาร์โค้ด", "ชื่อสินค้า", "หมวดหมู่",
                "ราคาทุน", "ราคาขายปกติ", "ราคาขายส่ง",
                "ราคาพิเศษ1", "ราคาพิเศษ2",
                "จำนวนสต็อก", "สต็อกขั้นต่ำ"
            ]
            sample_data = [
                {
                    "บาร์โค้ด": "8851234567890",
                    "ชื่อสินค้า": "สินค้าตัวอย่าง 1",
                    "หมวดหมู่": "อาหารและเครื่องดื่ม",
                    "ราคาทุน": 50.00,
                    "ราคาขายปกติ": 80.00,
                    "ราคาขายส่ง": 70.00,
                    "ราคาพิเศษ1": 75.00,
                    "ราคาพิเศษ2": 65.00,
                    "จำนวนสต็อก": 100,
                    "สต็อกขั้นต่ำ": 10
                },
                {
                    "บาร์โค้ด": "8851234567891",
                    "ชื่อสินค้า": "สินค้าตัวอย่าง 2",
                    "หมวดหมู่": "ของใช้ทั่วไป",
                    "ราคาทุน": 30.00,
                    "ราคาขายปกติ": 55.00,
                    "ราคาขายส่ง": 45.00,
                    "ราคาพิเศษ1": 50.00,
                    "ราคาพิเศษ2": 40.00,
                    "จำนวนสต็อก": 200,
                    "สต็อกขั้นต่ำ": 20
                }
            ]
            success = ExcelManager.export_to_excel(
                sample_data, columns, save_path,
                "สินค้า", "Template สำหรับนำเข้าสินค้า"
            )
            if success:
                messagebox.showinfo(
                    "สำเร็จ",
                    f"สร้างเทมเพลตสำเร็จ!\n\nบันทึกที่: {save_path}\n\n"
                    "วิธีใช้:\n"
                    "1. เปิดไฟล์แล้วกรอกข้อมูลสินค้า\n"
                    "2. ลบแถวตัวอย่างออก\n"
                    "3. กลับมากด 'นำเข้า Excel' เพื่อนำเข้า"
                )
                # เปิดโฟลเดอร์ที่บันทึก
                os.startfile(os.path.dirname(save_path))
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถสร้างเทมเพลตได้")
        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

    def import_products_action(self):
        """นำเข้าสินค้าจากไฟล์ Excel"""
        file_path = filedialog.askopenfilename(
            title="เลือกไฟล์ Excel สำหรับนำเข้าสินค้า",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not file_path:
            return

        # อ่านข้อมูลจาก Excel
        try:
            data = ExcelManager.import_from_excel(file_path, header_row=3)
        except Exception as e:
            messagebox.showerror("ผิดพลาด", f"ไม่สามารถอ่านไฟล์ได้:\n{e}")
            return

        if not data:
            messagebox.showwarning("ไม่มีข้อมูล", "ไม่พบข้อมูลในไฟล์ Excel\n\nตรวจสอบว่าข้อมูลเริ่มที่แถวที่ 5 (ใต้หัวตาราง)")
            return

        # แมปคอลัมน์ไทย → ฟิลด์ฐานข้อมูล
        col_map = {
            "บาร์โค้ด": "barcode",
            "ชื่อสินค้า": "product_name",
            "หมวดหมู่": "category",
            "ราคาทุน": "cost_price",
            "ราคาขายปกติ": "retail_price",
            "ราคาขายส่ง": "wholesale_price",
            "ราคาพิเศษ1": "special_price1",
            "ราคาพิเศษ2": "special_price2",
            "จำนวนสต็อก": "stock_quantity",
            "สต็อกขั้นต่ำ": "min_stock",
        }

        # ยืนยันก่อนนำเข้า
        confirm = messagebox.askyesno(
            "ยืนยันการนำเข้า",
            f"พบข้อมูล {len(data)} รายการในไฟล์\n\n"
            "ต้องการนำเข้าทั้งหมดหรือไม่?\n\n"
            "• หมวดหมู่ที่ไม่มีในระบบจะถูกสร้างอัตโนมัติ\n"
            "• สินค้าที่บาร์โค้ดซ้ำจะถูกข้าม"
        )
        if not confirm:
            return

        # เริ่มนำเข้า
        success_count = 0
        skipped_count = 0
        error_count = 0
        error_details = []

        self.db.connect()
        self.db.begin_transaction()

        try:
            # โหลด cache หมวดหมู่
            categories = self.db.fetch_all("SELECT category_id, category_name FROM categories")
            cat_lookup = {c['category_name']: c['category_id'] for c in categories} if categories else {}

            for idx, row in enumerate(data):
                try:
                    # แปลง key ภาษาไทย → อังกฤษ
                    mapped = {}
                    for thai_key, eng_key in col_map.items():
                        val = row.get(thai_key, None)
                        # pandas อ่าน NaN → ต้องจัดการ
                        if val is not None and str(val).strip() != '' and str(val).lower() != 'nan':
                            mapped[eng_key] = val
                        else:
                            mapped[eng_key] = None

                    # ต้องมีชื่อสินค้า
                    product_name = mapped.get("product_name")
                    if not product_name or str(product_name).strip() == '':
                        continue  # ข้ามแถวว่าง

                    product_name = str(product_name).strip()

                    # จัดการบาร์โค้ด
                    barcode = mapped.get("barcode")
                    if barcode:
                        barcode = str(barcode).strip().replace('.0', '')  # pandas อาจอ่านเป็น float

                    # เช็คบาร์โค้ดซ้ำ
                    if barcode:
                        existing = self.db.fetch_one(
                            "SELECT product_id FROM products WHERE barcode = ? AND is_active = 1",
                            (barcode,)
                        )
                        if existing:
                            skipped_count += 1
                            continue

                    # จัดการหมวดหมู่ — สร้างอัตโนมัติถ้าไม่มี
                    category_id = None
                    cat_name = mapped.get("category")
                    if cat_name and str(cat_name).strip():
                        cat_name = str(cat_name).strip()
                        if cat_name in cat_lookup:
                            category_id = cat_lookup[cat_name]
                        else:
                            # สร้างหมวดหมู่ใหม่
                            self.db.execute(
                                "INSERT INTO categories (category_name) VALUES (?)",
                                (cat_name,)
                            )
                            new_cat = self.db.fetch_one(
                                "SELECT category_id FROM categories WHERE category_name = ?",
                                (cat_name,)
                            )
                            if new_cat:
                                category_id = new_cat['category_id']
                                cat_lookup[cat_name] = category_id

                    # แปลงตัวเลข
                    def to_float(val, default=0):
                        try:
                            return float(val) if val else default
                        except (ValueError, TypeError):
                            return default

                    def to_int(val, default=0):
                        try:
                            return int(float(val)) if val else default
                        except (ValueError, TypeError):
                            return default

                    cost_price = to_float(mapped.get("cost_price"))
                    retail_price = to_float(mapped.get("retail_price"))
                    wholesale_price = to_float(mapped.get("wholesale_price"))
                    special_price1 = to_float(mapped.get("special_price1"))
                    special_price2 = to_float(mapped.get("special_price2"))
                    stock_qty = to_int(mapped.get("stock_quantity"))
                    min_stock = to_int(mapped.get("min_stock"), 10)

                    # INSERT สินค้า
                    result = self.db.execute("""
                        INSERT INTO products (
                            barcode, product_name, category_id,
                            cost_price, retail_price, wholesale_price,
                            special_price1, special_price2,
                            stock_quantity, min_stock, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (
                        barcode, product_name, category_id,
                        cost_price, retail_price, wholesale_price,
                        special_price1, special_price2,
                        stock_qty, min_stock
                    ))

                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                        error_details.append(f"แถว {idx+1}: {product_name} — {self.db.last_error}")

                except Exception as e:
                    error_count += 1
                    error_details.append(f"แถว {idx+1}: {str(e)}")

            # Commit ถ้ามีสินค้าที่นำเข้าสำเร็จ
            if success_count > 0:
                self.db.commit_transaction()
            else:
                self.db.rollback_transaction()

        except Exception as e:
            self.db.rollback_transaction()
            messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาดร้ายแรง:\n{e}")
            self.db.disconnect()
            return

        self.db.disconnect()

        # แสดงผลสรุป
        summary = (
            f"📊 ผลการนำเข้าสินค้า\n\n"
            f"✅ นำเข้าสำเร็จ: {success_count} รายการ\n"
            f"⏭️ ข้ามเพราะซ้ำ: {skipped_count} รายการ\n"
            f"❌ ผิดพลาด: {error_count} รายการ\n"
        )
        if error_details:
            summary += "\n--- รายละเอียดข้อผิดพลาด ---\n"
            summary += "\n".join(error_details[:10])  # แสดงแค่ 10 รายการแรก
            if len(error_details) > 10:
                summary += f"\n... และอีก {len(error_details) - 10} รายการ"

        if success_count > 0:
            messagebox.showinfo("ผลการนำเข้า", summary)
            # รีเฟรชรายการสินค้า
            self._categories_cache = None
            self.load_categories_cache()
            self.load_products()
        else:
            messagebox.showwarning("ผลการนำเข้า", summary)

    def setup_keyboard_shortcuts(self):
        """ตั้งค่า keyboard shortcuts สำหรับจัดการสินค้า"""
        # F5: เพิ่มสินค้าใหม่ (Wizard)
        self.bind("<F5>", lambda e: self.show_add_product_dialog())

        # Ctrl+F: Focus ช่องค้นหา
        self.bind("<Control-f>", lambda e: self.search_entry.focus())
        
        # Ctrl+N: เพิ่มสินค้าใหม่ (เหมือน F5)
        self.bind("<Control-n>", lambda e: self.show_add_product_dialog())
        
        # Ctrl+R: Refresh
        self.bind("<Control-r>", lambda e: self.load_products())
        
        # ทำให้ frame focus ได้
        self.focus_set()
    
    def load_image_optimized(self, image_path, size=(80, 80)):
        """โหลดรูปภาพแบบ optimized พร้อม cache"""
        if not image_path or not os.path.exists(image_path):
            return None
        
        # ตรวจสอบ cache ก่อน
        cache_key = f"{image_path}_{size[0]}x{size[1]}"
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]
        
        try:
            # โหลดและ resize (ใช้ BILINEAR เร็วกว่า LANCZOS 3x)
            img = Image.open(image_path)
            img.thumbnail(size, Image.Resampling.BILINEAR)
            photo = ImageTk.PhotoImage(img)
            
            # เก็บใน cache (ใช้ค่าจาก config)
            max_cache = PERFORMANCE_MODE.get("max_cached_images", 20)
            try:
                import performance_config
                max_cache = performance_config.MAX_IMAGE_CACHE_SIZE
            except ImportError:
                pass
            if len(self._image_cache) > max_cache:
                # ลบรูปเก่าสุด
                first_key = next(iter(self._image_cache))
                del self._image_cache[first_key]
            
            self._image_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def show_barcode_print_dialog(self):
        """เปิดหน้าต่างตั้งค่าพิมพ์บาร์โค้ดสินค้า"""
        BarcodePrintDialog(self)


class BarcodePrintDialog(ctk.CTkToplevel):
    """หน้าต่างสำหรับตั้งค่าและสั่งพิมพ์บาร์โค้ดแบบดวงตาราง"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.db = parent.db
        
        self.title("ระบบพิมพ์ป้ายบาร์โค้ดสินค้า (Bulk Barcode Label Printer)")
        self.geometry("980x680")
        self.resizable(True, True)
        
        # ตั้งค่าให้อยู่ตรงกลางจอและแย่ง focus
        self.transient(parent)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 980) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f"+{x}+{y}")
        
        # จัดเก็บรายการสินค้าที่จะพิมพ์ {product_id: item_dict}
        self.selected_items = {}
        
        self.create_widgets()
        
    def create_widgets(self):
        # แผงแบ่งสองคอลัมน์ ซ้าย (ค้นหาและตารางรายการ) ขวา (การตั้งค่าพิมพ์)
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.pack(fill="both", expand=True, padx=15, pady=15)
        
        # ===== คอลัมน์ซ้าย: ค้นหา + รายการที่จะพิมพ์ =====
        left_column = ctk.CTkFrame(main_split, fg_color="white", corner_radius=12)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # หัวเรื่องซ้าย
        left_title = ctk.CTkLabel(
            left_column, 
            text="📋 รายการป้ายสินค้าที่ต้องการจัดพิมพ์", 
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["primary"]
        )
        left_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        # ช่องค้นหาสินค้าเพื่อเพิ่มในตารางพิมพ์
        search_label = ctk.CTkLabel(
            left_column,
            text="🔍 พิมพ์ชื่อสินค้า หรือยิงบาร์โค้ด เพื่อเพิ่มรายการ:",
            font=("Sarabun", 14),
            text_color=COLORS["text_dark"]
        )
        search_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        self.search_entry = ctk.CTkEntry(
            left_column,
            placeholder_text="ค้นหาสินค้าตรงนี้...",
            font=("Sarabun", 14),
            height=40
        )
        self.search_entry.pack(fill="x", padx=15, pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        
        # Scrollable สำหรับแสดงผลลัพธ์การค้นหา
        self.results_scroll = ctk.CTkScrollableFrame(
            left_column, 
            height=120, 
            fg_color="#f5f6fa",
            corner_radius=8
        )
        # ซ่อนไว้เริ่มต้น จะแสดงเฉพาะเมื่อพิมพ์ค้นหา
        
        # คอนเทนเนอร์ตารางรายการสินค้าที่จะพิมพ์
        table_header = ctk.CTkFrame(left_column, fg_color="#f1f2f6", height=32, corner_radius=4)
        table_header.pack(fill="x", padx=15, pady=(10, 0))
        table_header.pack_propagate(False)
        
        ctk.CTkLabel(table_header, text="ชื่อสินค้า", font=("Sarabun", 13, "bold"), text_color=COLORS["text_dark"]).pack(side="left", padx=10)
        ctk.CTkLabel(table_header, text="จัดการจำนวนพิมพ์", font=("Sarabun", 13, "bold"), text_color=COLORS["text_dark"]).pack(side="right", padx=100)
        
        self.table_scroll = ctk.CTkScrollableFrame(left_column, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.update_table_display()
        
        # ===== คอลัมน์ขวา: การตั้งค่า Layout + ปุ่ม Print =====
        right_column = ctk.CTkFrame(main_split, width=320, fg_color="#f8f9fa", corner_radius=12)
        right_column.pack(side="right", fill="y", expand=False)
        right_column.pack_propagate(False)
        
        right_title = ctk.CTkLabel(
            right_column, 
            text="⚙️ ตั้งค่ากระดาษ & Layout", 
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["primary"]
        )
        right_title.pack(anchor="w", padx=15, pady=(15, 15))
        
        # รูปแบบตาราง / Layout
        layout_label = ctk.CTkLabel(
            right_column,
            text="รูปแบบช่องตาราง (ขนาด A4):",
            font=("Sarabun", 14, "bold"),
            text_color=COLORS["text_dark"]
        )
        layout_label.pack(anchor="w", padx=15, pady=(5, 2))
        
        self.layout_combo = ctk.CTkComboBox(
            right_column,
            values=[
                "A4: 3 คอลัมน์ x 10 แถว (30 ดวง/หน้า)",
                "A4: 4 คอลัมน์ x 12 แถว (48 ดวง/หน้า)",
                "A4: 5 คอลัมน์ x 15 แถว (75 ดวง/หน้า)"
            ],
            font=("Sarabun", 14),
            height=35,
            width=280,
            state="readonly"
        )
        self.layout_combo.set("A4: 3 คอลัมน์ x 10 แถว (30 ดวง/หน้า)")
        self.layout_combo.pack(anchor="w", padx=15, pady=(0, 15))
        
        # ตัวเลือกฟิลด์ข้อมูลที่จะพิมพ์
        options_label = ctk.CTkLabel(
            right_column,
            text="ข้อมูลที่จะแสดงบนป้าย:",
            font=("Sarabun", 14, "bold"),
            text_color=COLORS["text_dark"]
        )
        options_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        self.show_name_var = ctk.BooleanVar(value=True)
        self.show_name_cb = ctk.CTkCheckBox(
            right_column, text="แสดงชื่อสินค้า", font=("Sarabun", 14),
            variable=self.show_name_var, text_color=COLORS["text_dark"]
        )
        self.show_name_cb.pack(anchor="w", padx=20, pady=5)
        
        self.show_price_var = ctk.BooleanVar(value=True)
        self.show_price_cb = ctk.CTkCheckBox(
            right_column, text="แสดงราคาสินค้า", font=("Sarabun", 14),
            variable=self.show_price_var, text_color=COLORS["text_dark"]
        )
        self.show_price_cb.pack(anchor="w", padx=20, pady=5)
        
        self.show_code_var = ctk.BooleanVar(value=True)
        self.show_code_cb = ctk.CTkCheckBox(
            right_column, text="แสดงบาร์โค้ดใต้รูป", font=("Sarabun", 14),
            variable=self.show_code_var, text_color=COLORS["text_dark"]
        )
        self.show_code_cb.pack(anchor="w", padx=20, pady=5)
        
        # ส่วนท้าย: ปุ่มดำเนินการ
        button_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        button_frame.pack(fill="x", side="bottom", padx=15, pady=20)
        
        self.preview_btn = ctk.CTkButton(
            button_frame,
            text="🧪 แสดงตัวอย่างใบพิมพ์ (PDF)",
            font=("Sarabun", 16, "bold"),
            height=45,
            fg_color=COLORS["success"],
            hover_color="#45a049",
            command=self.generate_labels_preview
        )
        self.preview_btn.pack(fill="x", pady=(0, 10))
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="✕ ปิดหน้าต่าง",
            font=("Sarabun", 15),
            height=35,
            fg_color=COLORS["text_light"],
            hover_color="#95a5a6",
            command=self.destroy
        )
        close_btn.pack(fill="x")
        
    def _on_search_key(self, event=None):
        query = self.search_entry.get().strip().lower()
        
        # ล้างผลการค้นหาเก่า
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
            
        if not query:
            self.results_scroll.pack_forget()
            return
            
        try:
            self.db.connect()
            products = self.db.fetch_all("""
                SELECT product_id, barcode, product_name, retail_price, stock_quantity
                FROM products
                WHERE is_active = 1
                AND (LOWER(product_name) LIKE ? OR LOWER(barcode) LIKE ?)
                LIMIT 6
            """, (f"%{query}%", f"%{query}%"))
            self.db.disconnect()
        except Exception as e:
            print(f"Search product error: {e}")
            products = []
            
        if products:
            self.results_scroll.pack(fill="x", after=self.search_entry, padx=15, pady=(2, 10))
            for p in products:
                # ปุ่มผลการค้นหา
                btn = ctk.CTkButton(
                    self.results_scroll,
                    text=f"➕ {p['product_name']} ({p['barcode'] or 'ไม่มีรหัส'}) - ฿{p['retail_price']:,.2f} [คลัง: {p['stock_quantity']}]",
                    anchor="w",
                    fg_color="transparent",
                    text_color=COLORS["text_dark"],
                    hover_color="#e1e2e6",
                    height=32,
                    font=("Sarabun", 13),
                    command=lambda prod=p: self.add_product_to_print(prod)
                )
                btn.pack(fill="x", padx=5, pady=1)
        else:
            self.results_scroll.pack_forget()
            
    def add_product_to_print(self, product):
        pid = product['product_id']
        barcode = product['barcode']
        
        if not barcode:
            messagebox.showwarning("ไม่มีรหัสบาร์โค้ด", f"สินค้า '{product['product_name']}' ไม่มีรหัสบาร์โค้ด ไม่สามารถเพิ่มรายการพิมพ์ได้")
            return
            
        if pid not in self.selected_items:
            # เริ่มต้นดึงจำนวนจากคลัง หากคลังเป็น 0 หรือน้อยกว่า ให้เริ่มที่ 10 ดวง
            default_qty = product['stock_quantity'] if product['stock_quantity'] > 0 else 10
            # ลิมิตเริ่มต้นไม่ให้มากเกินไป
            default_qty = min(default_qty, 30)
            
            self.selected_items[pid] = {
                'product_id': pid,
                'product_name': product['product_name'],
                'barcode': barcode,
                'retail_price': product['retail_price'],
                'stock_quantity': product['stock_quantity'],
                'quantity': default_qty
            }
        else:
            # บวกเพิ่ม 10 ดวงถ้ากดย้ำ
            self.selected_items[pid]['quantity'] += 10
            
        self.search_entry.delete(0, 'end')
        self.results_scroll.pack_forget()
        self.update_table_display()
        
    def remove_item(self, pid):
        if pid in self.selected_items:
            del self.selected_items[pid]
            self.update_table_display()
            
    def update_table_display(self):
        # ล้าง widget ในตารางเก่า
        for widget in self.table_scroll.winfo_children():
            widget.destroy()
            
        if not self.selected_items:
            empty_lbl = ctk.CTkLabel(
                self.table_scroll,
                text="⚠️ ยังไม่มีรายการสินค้าที่จะพิมพ์\nกรุณาพิมพ์ชื่อสินค้าเพื่อค้นหาและเพิ่มรายการด้านบน",
                font=("Sarabun", 14),
                text_color=COLORS["text_light"],
                justify="center"
            )
            empty_lbl.pack(fill="both", expand=True, pady=60)
            return
            
        for pid, item in self.selected_items.items():
            row_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row_frame.pack(fill="x", pady=4, padx=5)
            
            # คอลัมน์ซ้าย: ชื่อสินค้า + บาร์โค้ด
            name_lbl = ctk.CTkLabel(
                row_frame,
                text=f"{item['product_name']}\n(รหัสบาร์โค้ด: {item['barcode']})",
                font=("Sarabun", 14),
                text_color=COLORS["text_dark"],
                anchor="w",
                justify="left"
            )
            name_lbl.pack(side="left", padx=10)
            
            # คอลัมน์ขวา: ปุ่มควบคุมจำนวนพิมพ์ + ปุ่มลบ
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.pack(side="right", padx=5)
            
            # ปุ่มลบ 🗑️
            del_btn = ctk.CTkButton(
                actions_frame,
                text="🗑️",
                width=30,
                height=30,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                font=("Arial", 12),
                command=lambda p_id=pid: self.remove_item(p_id)
            )
            del_btn.pack(side="right", padx=(10, 0))
            
            # ปุ่มบวก ➕
            plus_btn = ctk.CTkButton(
                actions_frame,
                text="+",
                width=30,
                height=30,
                fg_color=COLORS["primary"],
                font=("Arial", 14, "bold"),
                command=lambda p_id=pid: self.adjust_qty(p_id, 1)
            )
            plus_btn.pack(side="right")
            
            # Entry กรอกจำนวน
            qty_var = ctk.StringVar(value=str(item['quantity']))
            qty_entry = ctk.CTkEntry(
                actions_frame,
                width=50,
                height=30,
                font=("Sarabun", 13),
                justify="center",
                textvariable=qty_var
            )
            qty_entry.pack(side="right", padx=5)
            
            # ดักจับเมื่อผู้ใช้พิมพ์แก้ไขเอง
            def make_validate_cmd(p_id=pid, var=qty_var):
                def validate_input(*args):
                    try:
                        val = int(var.get())
                        if val < 1:
                            val = 1
                        self.selected_items[p_id]['quantity'] = val
                    except ValueError:
                        pass
                return validate_input
            
            qty_var.trace_add("write", make_validate_cmd(pid, qty_var))
            
            # ปุ่มลบ ➖
            minus_btn = ctk.CTkButton(
                actions_frame,
                text="-",
                width=30,
                height=30,
                fg_color=COLORS["primary"],
                font=("Arial", 14, "bold"),
                command=lambda p_id=pid: self.adjust_qty(p_id, -1)
            )
            minus_btn.pack(side="right")
            
            # แสดงข้อมูลสต็อกและราคาคร่าวๆ
            stock_lbl = ctk.CTkLabel(
                actions_frame,
                text=f"สต็อก: {item['stock_quantity']} ดวง  ",
                font=("Sarabun", 12),
                text_color=COLORS["text_light"]
            )
            stock_lbl.pack(side="right", padx=10)
            
            # เส้นคั่นระหว่างแถว
            divider = ctk.CTkFrame(self.table_scroll, fg_color="#e1e2e6", height=1)
            divider.pack(fill="x", pady=2)
            
    def adjust_qty(self, pid, diff):
        if pid in self.selected_items:
            new_qty = self.selected_items[pid]['quantity'] + diff
            if new_qty < 1:
                new_qty = 1
            self.selected_items[pid]['quantity'] = new_qty
            self.update_table_display()
            
    def generate_labels_preview(self):
        if not self.selected_items:
            messagebox.showwarning("ยังไม่ได้เลือกสินค้า", "กรุณาเพิ่มรายการสินค้าที่จะพิมพ์ลงในตารางก่อนดำเนินการต่อ")
            return
            
        # หาขนาดกริดตามที่เลือก
        layout_str = self.layout_combo.get()
        if "3 คอลัมน์" in layout_str:
            cols, rows = 3, 10
        elif "4 คอลัมน์" in layout_str:
            cols, rows = 4, 12
        else:
            cols, rows = 5, 15
            
        show_name = self.show_name_var.get()
        show_price = self.show_price_var.get()
        show_code = self.show_code_var.get()
        
        # แปลงเป็น list สำหรับการสร้างไฟล์
        items_list = list(self.selected_items.values())
        
        # ลิสต์ไฟล์ที่จะเซฟชั่วคราว
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = temp_dir / "barcode_labels_preview.pdf"
        
        # ปิดปุ่มระหว่างทำงานเพื่อความปลอดภัย
        self.preview_btn.configure(state="disabled", text="⏳ กำลังสร้างไฟล์ PDF...")
        self.update()
        
        success = create_barcode_labels_pdf(
            items_list, 
            str(pdf_path), 
            cols=cols, 
            rows=rows, 
            show_name=show_name, 
            show_price=show_price, 
            show_code=show_code
        )
        
        self.preview_btn.configure(state="normal", text="🧪 แสดงตัวอย่างใบพิมพ์ (PDF)")
        
        if success:
            try:
                # เปิดพรีวิวไฟล์ PDF ขึ้นมาเพื่อให้ผู้ใช้สั่งพิมพ์ผ่านโปรแกรมอ่าน PDF
                os.startfile(str(pdf_path.resolve()))
                # แสดงข้อความสำเร็จ
                messagebox.showinfo(
                    "สร้างไฟล์พรีวิวสำเร็จ",
                    f"สร้างไฟล์ PDF ตัวอย่างบาร์โค้ดเรียบร้อยแล้ว\n"
                    f"ระบบได้เปิดไฟล์บาร์โค้ดให้ท่านแล้ว ท่านสามารถสั่งพิมพ์ผ่านโปรแกรมเปิด PDF ได้ทันที\n"
                    f"(หรือพิมพ์ขนาด A4 เพื่อทดสอบดวงสติ๊กเกอร์ของท่าน)"
                )
            except Exception as e:
                messagebox.showerror(
                    "เกิดข้อผิดพลาด",
                    f"สร้างไฟล์ PDF สำเร็จแต่ไม่สามารถเปิดพรีวิวโดยอัตโนมัติได้:\n{e}\n"
                    f"กรุณาเปิดไฟล์เองที่: {pdf_path.resolve()}"
                )
        else:
            messagebox.showerror("เกิดข้อผิดพลาด", "ระบบไม่สามารถสร้างไฟล์ PDF บาร์โค้ดได้ กรุณาลองใหม่อีกครั้ง")

