# -*- coding: utf-8 -*-
"""
หน้าจัดการสต็อกสินค้า
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
from datetime import datetime


class StockManagementFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการสต็อกสินค้า"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        self._search_timer = None  # Debounce timer for search (BUG-015)
        self.create_widgets()
        self.load_products()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text="📦 จัดการสต็อกสินค้า",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 รีเฟรช",
            font=FONTS["button"],
            width=120,
            height=40,
            fg_color=COLORS["info"],
            command=self.load_products
        )
        refresh_btn.pack(side="right", padx=5)
        
        # ส่วนค้นหาและกรอง
        filter_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        filter_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # ค้นหา
        ctk.CTkLabel(
            filter_frame,
            text="🔍 ค้นหา:",
            font=FONTS["body"]
        ).pack(side="left", padx=(20, 10), pady=15)
        
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="ชื่อสินค้า หรือ บาร์โค้ด...",
            font=FONTS["body"],
            width=300,
            height=40
        )
        self.search_entry.pack(side="left", padx=5, pady=15)
        self.search_entry.bind("<KeyRelease>", lambda e: self._debounce_search())
        
        # กรองสถานะสต็อก
        ctk.CTkLabel(
            filter_frame,
            text="สถานะ:",
            font=FONTS["body"]
        ).pack(side="left", padx=(30, 10))
        
        self.status_var = ctk.StringVar(value="ทั้งหมด")
        status_combo = ctk.CTkComboBox(
            filter_frame,
            values=["ทั้งหมด", "สต็อกปกติ", "สต็อกต่ำ", "สต็อกหมด"],
            variable=self.status_var,
            width=150,
            font=FONTS["body"],
            command=lambda x: self.load_products()
        )
        status_combo.pack(side="left", padx=5)
        
        # สถิติสรุป
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.total_products_card = self.create_stat_card(
            stats_frame, "📦 สินค้าทั้งหมด", "0", COLORS["info"]
        )
        self.total_products_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.low_stock_card = self.create_stat_card(
            stats_frame, "⚠️ สต็อกต่ำ", "0", COLORS["warning"]
        )
        self.low_stock_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.out_stock_card = self.create_stat_card(
            stats_frame, "❌ สต็อกหมด", "0", COLORS["danger"]
        )
        self.out_stock_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.total_value_card = self.create_stat_card(
            stats_frame, "💰 มูลค่าสต็อก", "฿0", COLORS["success"]
        )
        self.total_value_card.pack(side="left", fill="x", expand=True, padx=5)
        
        # ตารางรายการ
        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Header ตาราง
        header_row = ctk.CTkFrame(table_frame, fg_color=COLORS["primary"])
        header_row.pack(fill="x")
        
        headers = [
            ("บาร์โค้ด", 120),
            ("ชื่อสินค้า", 250),
            ("หมวดหมู่", 120),
            ("สต็อกปัจจุบัน", 100),
            ("สต็อกต่ำสุด", 100),
            ("ต้นทุน/หน่วย", 100),
            ("มูลค่า", 100),
            ("สถานะ", 100),
            ("จัดการ", 200)
        ]
        
        for header, width in headers:
            label = ctk.CTkLabel(
                header_row,
                text=header,
                font=FONTS["button"],
                text_color="white",
                width=width
            )
            label.pack(side="left", padx=5, pady=10)
        
        # รายการ
        self.products_container = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="white"
        )
        self.products_container.pack(fill="both", expand=True)
        
    def create_stat_card(self, parent, title, value, color):
        """สร้างการ์ดสถิติ"""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=FONTS["body"],
            text_color="white"
        )
        title_label.pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Sarabun", 24, "bold"),
            text_color="white"
        )
        value_label.pack(pady=(0, 15))
        
        card.value_label = value_label
        return card
    
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
        self._search_timer = self.after(ms, self.load_products)
    
    def load_products(self):
        """โหลดรายการสินค้า"""
        # ล้างรายการเดิม
        for widget in self.products_container.winfo_children():
            widget.destroy()
        
        # สร้าง query
        search = self.search_entry.get().strip()
        status = self.status_var.get()
        
        query = """
            SELECT p.*, c.category_name,
                   (p.stock_quantity * p.cost_price) as stock_value
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.category_id
            WHERE p.is_active = 1
        """
        params = []
        
        if search:
            query += " AND (p.product_name LIKE ? OR p.barcode LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        if status == "สต็อกต่ำ":
            query += " AND p.stock_quantity > 0 AND p.stock_quantity <= p.min_stock"
        elif status == "สต็อกหมด":
            query += " AND p.stock_quantity = 0"
        elif status == "สต็อกปกติ":
            query += " AND p.stock_quantity > p.min_stock"
        
        query += " ORDER BY p.stock_quantity ASC"
        
        # ดึงข้อมูล
        self.db.connect()
        products = self.db.fetch_all(query, params if params else None)
        self.db.disconnect()
        
        # คำนวณสถิติ
        total_products = len(products)
        low_stock = sum(1 for p in products if 0 < p['stock_quantity'] <= p['min_stock'])
        out_stock = sum(1 for p in products if p['stock_quantity'] == 0)
        total_value = sum(p['stock_value'] for p in products)
        
        # อัพเดทสถิติ
        self.total_products_card.value_label.configure(text=f"{total_products}")
        self.low_stock_card.value_label.configure(text=f"{low_stock}")
        self.out_stock_card.value_label.configure(text=f"{out_stock}")
        self.total_value_card.value_label.configure(text=f"฿{total_value:,.2f}")
        
        if not products:
            no_data = ctk.CTkLabel(
                self.products_container,
                text="ไม่พบข้อมูลสินค้า",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            )
            no_data.pack(pady=50)
            return
        
        # แสดงรายการ
        for idx, product in enumerate(products):
            self.create_product_row(product, idx)
    
    def create_product_row(self, product, index):
        """สร้างแถวรายการสินค้า"""
        bg_color = COLORS["light"] if index % 2 == 0 else "white"
        
        row = ctk.CTkFrame(self.products_container, fg_color=bg_color, height=60)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # บาร์โค้ด
        ctk.CTkLabel(
            row,
            text=product['barcode'],
            font=FONTS["body"],
            width=120
        ).pack(side="left", padx=5)
        
        # ชื่อสินค้า
        ctk.CTkLabel(
            row,
            text=product['product_name'][:30],
            font=FONTS["body"],
            width=250,
            anchor="w"
        ).pack(side="left", padx=5)
        
        # หมวดหมู่
        ctk.CTkLabel(
            row,
            text=product['category_name'] or '-',
            font=FONTS["body"],
            width=120
        ).pack(side="left", padx=5)
        
        # สต็อกปัจจุบัน
        stock_qty = product['stock_quantity']
        min_stock = product['min_stock']
        
        stock_color = COLORS["text_dark"]
        if stock_qty == 0:
            stock_color = COLORS["danger"]
        elif stock_qty <= min_stock:
            stock_color = COLORS["warning"]
        else:
            stock_color = COLORS["success"]
        
        ctk.CTkLabel(
            row,
            text=f"{stock_qty}",
            font=("Sarabun", 16, "bold"),
            width=100,
            text_color=stock_color
        ).pack(side="left", padx=5)
        
        # สต็อกต่ำสุด
        ctk.CTkLabel(
            row,
            text=str(min_stock),
            font=FONTS["body"],
            width=100
        ).pack(side="left", padx=5)
        
        # ต้นทุน
        ctk.CTkLabel(
            row,
            text=f"฿{product['cost_price']:,.2f}",
            font=FONTS["body"],
            width=100
        ).pack(side="left", padx=5)
        
        # มูลค่า
        ctk.CTkLabel(
            row,
            text=f"฿{product['stock_value']:,.2f}",
            font=("Sarabun", 14, "bold"),
            width=100,
            text_color=COLORS["success"]
        ).pack(side="left", padx=5)
        
        # สถานะ
        if stock_qty == 0:
            status_text = "หมด"
            status_color = COLORS["danger"]
        elif stock_qty <= min_stock:
            status_text = "ต่ำ"
            status_color = COLORS["warning"]
        else:
            status_text = "ปกติ"
            status_color = COLORS["success"]
        
        status_label = ctk.CTkLabel(
            row,
            text=status_text,
            font=FONTS["body"],
            width=100,
            fg_color=status_color,
            corner_radius=5,
            text_color="white"
        )
        status_label.pack(side="left", padx=5)
        
        # ปุ่มจัดการ
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=200)
        btn_frame.pack(side="left", padx=5)
        btn_frame.pack_propagate(False)
        
        # ปุ่มแก้ไขจำนวนโดยตรง (ใช้ง่ายที่สุด)
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color="#6c5ce7",
            hover_color="#5a4bd1",
            command=lambda p=product: self.set_stock(p)
        )
        edit_btn.pack(side="left", padx=2)
        
        add_btn = ctk.CTkButton(
            btn_frame,
            text="➕",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["success"],
            command=lambda p=product: self.adjust_stock(p, "add")
        )
        add_btn.pack(side="left", padx=2)
        
        remove_btn = ctk.CTkButton(
            btn_frame,
            text="➖",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["danger"],
            command=lambda p=product: self.adjust_stock(p, "remove")
        )
        remove_btn.pack(side="left", padx=2)
        
        history_btn = ctk.CTkButton(
            btn_frame,
            text="📋",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["info"],
            command=lambda p=product: self.view_stock_history(p)
        )
        history_btn.pack(side="left", padx=2)
    
    def set_stock(self, product):
        """ตั้งค่าจำนวนสต็อกโดยตรง — ใช้ง่ายสำหรับผู้สูงอายุ"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"แก้ไขจำนวนสต็อก")
        dialog.geometry("500x480")
        dialog.transient(self)
        dialog.grab_set()
        
        # หัวข้อใหญ่
        header = ctk.CTkFrame(dialog, fg_color="#6c5ce7", corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="✏️ แก้ไขจำนวนสต็อก",
            font=("Sarabun", 22, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        # ข้อมูลสินค้า
        info_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        info_frame.pack(fill="x", padx=25, pady=20)
        
        ctk.CTkLabel(
            info_frame,
            text=f"สินค้า: {product['product_name']}",
            font=("Sarabun", 18, "bold"),
            wraplength=400,
            justify="left"
        ).pack(padx=20, pady=(15, 5), anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=f"บาร์โค้ด: {product['barcode'] or '-'}",
            font=("Sarabun", 16),
        ).pack(padx=20, pady=(0, 5), anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=f"จำนวนปัจจุบัน:  {product['stock_quantity']}  ชิ้น",
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["primary"]
        ).pack(padx=20, pady=(5, 15), anchor="w")
        
        # ช่องกรอกจำนวนใหม่ — ตัวใหญ่มาก
        ctk.CTkLabel(
            dialog,
            text="กรอกจำนวนสต็อกใหม่:",
            font=("Sarabun", 18, "bold")
        ).pack(pady=(15, 5))
        
        new_qty_entry = ctk.CTkEntry(
            dialog,
            font=("Sarabun", 32, "bold"),
            height=70,
            width=250,
            justify="center",
            placeholder_text="0"
        )
        new_qty_entry.pack(pady=10)
        new_qty_entry.insert(0, str(product['stock_quantity']))
        new_qty_entry.focus()
        new_qty_entry.select_range(0, 'end')
        
        # ปุ่มบันทึก
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_new_stock(event=None):
            try:
                new_qty = int(new_qty_entry.get().strip())
                if new_qty < 0:
                    messagebox.showerror("ข้อผิดพลาด", "จำนวนสต็อกต้องไม่ติดลบ")
                    return
                    
                old_qty = product['stock_quantity']
                diff = new_qty - old_qty
                
                self.db.connect()
                
                # อัปเดตสต็อก
                success = self.db.execute(
                    "UPDATE products SET stock_quantity = ? WHERE product_id = ?",
                    (new_qty, product['product_id'])
                )
                
                if not success:
                    self.db.disconnect()
                    messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถอัปเดตสต็อกได้")
                    return
                
                # บันทึกประวัติการเคลื่อนไหว
                if diff != 0:
                    movement_type = 'in' if diff > 0 else 'out'
                    self.db.execute("""
                        INSERT INTO stock_movements (
                            product_id, movement_type, quantity,
                            reference_type, user_id, notes
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        product['product_id'], movement_type, abs(diff),
                        'manual_adjustment', self.user_id,
                        f"ตั้งค่าสต็อกจาก {old_qty} เป็น {new_qty}"
                    ))
                
                self.db.disconnect()
                
                messagebox.showinfo(
                    "สำเร็จ",
                    f"อัปเดตสต็อกเรียบร้อย!\n{product['product_name']}\n{old_qty} → {new_qty} ชิ้น"
                )
                dialog.destroy()
                self.load_products()
                
            except ValueError:
                messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกตัวเลขที่ถูกต้อง")
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾  บันทึก",
            font=("Sarabun", 20, "bold"),
            width=180,
            height=55,
            fg_color="#6c5ce7",
            hover_color="#5a4bd1",
            command=save_new_stock
        )
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="ยกเลิก",
            font=("Sarabun", 18),
            width=120,
            height=55,
            fg_color=COLORS["text_light"],
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=10)
        
        # กด Enter เพื่อบันทึก
        new_qty_entry.bind("<Return>", save_new_stock)
        dialog.bind("<Return>", save_new_stock)

    def adjust_stock(self, product, action):
        """ปรับสต็อก"""
        dialog = ctk.CTkToplevel(self)
        
        if action == "add":
            dialog.title(f"เพิ่มสต็อก - {product['product_name']}")
            label_text = "จำนวนที่ต้องการเพิ่ม:"
            btn_text = "➕ เพิ่มสต็อก"
            btn_color = COLORS["success"]
        else:
            dialog.title(f"ลดสต็อก - {product['product_name']}")
            label_text = "จำนวนที่ต้องการลด:"
            btn_text = "➖ ลดสต็อก"
            btn_color = COLORS["danger"]
        
        dialog.geometry("500x550")
        dialog.transient(self)
        dialog.grab_set()
        
        # ข้อมูลสินค้า
        info_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        info_text = f"""
        สินค้า: {product['product_name']}
        บาร์โค้ด: {product['barcode']}
        สต็อกปัจจุบัน: {product['stock_quantity']} {product['unit']}
        """
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=FONTS["body"],
            justify="left"
        ).pack(padx=20, pady=20)
        
        # จำนวน
        ctk.CTkLabel(
            dialog,
            text=label_text,
            font=FONTS["body"]
        ).pack(pady=(10, 5))
        
        quantity_entry = ctk.CTkEntry(
            dialog,
            font=("Sarabun", 18),
            height=50,
            width=200,
            justify="center"
        )
        quantity_entry.pack(pady=5)
        quantity_entry.insert(0, "1")
        quantity_entry.focus()
        
        # หมายเหตุ
        ctk.CTkLabel(
            dialog,
            text="หมายเหตุ:",
            font=FONTS["body"]
        ).pack(pady=(20, 5))
        
        notes_entry = ctk.CTkTextbox(
            dialog,
            font=FONTS["body"],
            height=80
        )
        notes_entry.pack(fill="x", padx=20, pady=5)
        
        # ปุ่ม
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_adjustment():
            try:
                quantity = int(quantity_entry.get())
                if quantity <= 0:
                    messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกจำนวนที่มากกว่า 0")
                    return
                
                if action == "remove" and quantity > product['stock_quantity']:
                    messagebox.showerror(
                        "ข้อผิดพลาด",
                        f"สต็อกไม่พอ (มีอยู่ {product['stock_quantity']})"
                    )
                    return
                
                notes = notes_entry.get("1.0", "end").strip()
                
                # บันทึก
                # บันทึก
                self.db.connect()
                
                # ดึงข้อมูลล่าสุดจากฐานข้อมูลเพื่อความถูกต้อง
                current_product = self.db.fetch_one(
                    "SELECT stock_quantity FROM products WHERE product_id = ?", 
                    (product['product_id'],)
                )
                
                if not current_product:
                    self.db.disconnect()
                    messagebox.showerror("ข้อผิดพลาด", "ไม่พบข้อมูลสินค้าล่าสุด")
                    return
                    
                current_stock = current_product['stock_quantity']
                
                # อัพเดทสต็อก
                if action == "add":
                    new_stock = current_stock + quantity
                    movement_type = 'in'
                else:
                    if quantity > current_stock:
                        self.db.disconnect()
                        messagebox.showerror("ข้อผิดพลาด", f"สต็อกไม่พอ (มีอยู่ {current_stock})")
                        return
                    new_stock = current_stock - quantity
                    movement_type = 'out'
                
                success_update = self.db.execute(
                    "UPDATE products SET stock_quantity = ? WHERE product_id = ?",
                    (new_stock, product['product_id'])
                )
                
                if not success_update:
                    self.db.disconnect()
                    messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถอัพเดทสต็อกได้")
                    return
                
                # บันทึกการเคลื่อนไหว
                self.db.execute("""
                    INSERT INTO stock_movements (
                        product_id, movement_type, quantity,
                        reference_type, user_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    product['product_id'], movement_type, quantity,
                    'manual_adjustment', self.user_id, notes
                ))
                
                self.db.disconnect()
                
                messagebox.showinfo("สำเร็จ", "ปรับสต็อกสำเร็จ!")
                dialog.destroy()
                self.load_products()
                
            except ValueError:
                messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกจำนวนที่ถูกต้อง")
        
        ctk.CTkButton(
            btn_frame,
            text=btn_text,
            font=("Sarabun", 16, "bold"),
            width=150,
            height=45,
            fg_color=btn_color,
            command=save_adjustment
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="ยกเลิก",
            font=FONTS["button"],
            width=100,
            height=45,
            fg_color=COLORS["text_light"],
            command=dialog.destroy
        ).pack(side="left", padx=5)
    
    def view_stock_history(self, product):
        """ดูประวัติการเคลื่อนไหวสต็อก"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"ประวัติสต็อก - {product['product_name']}")
        dialog.geometry("900x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color=COLORS["primary"])
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text=f"📋 ประวัติการเคลื่อนไหว - {product['product_name']}",
            font=FONTS["heading"],
            text_color="white"
        ).pack(pady=15)
        
        # ตารางประวัติ
        table_frame = ctk.CTkScrollableFrame(dialog, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ดึงข้อมูล
        self.db.connect()
        movements = self.db.fetch_all("""
            SELECT sm.*, u.full_name
            FROM stock_movements sm
            LEFT JOIN users u ON sm.user_id = u.user_id
            WHERE sm.product_id = ?
            ORDER BY sm.movement_id DESC
            LIMIT 100
        """, (product['product_id'],))
        self.db.disconnect()
        
        if not movements:
            ctk.CTkLabel(
                table_frame,
                text="ยังไม่มีประวัติการเคลื่อนไหว",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            ).pack(pady=50)
            return
        
        # Header
        header_row = ctk.CTkFrame(table_frame, fg_color=COLORS["light"])
        header_row.pack(fill="x", pady=(0, 10))
        
        headers = ["วันที่/เวลา", "ประเภท", "จำนวน", "อ้างอิง", "ผู้ดำเนินการ", "หมายเหตุ"]
        for header in headers:
            ctk.CTkLabel(
                header_row,
                text=header,
                font=FONTS["button"],
                width=140
            ).pack(side="left", padx=5, pady=10)
        
        # รายการ
        for movement in movements:
            row = ctk.CTkFrame(table_frame, fg_color="white", corner_radius=5)
            row.pack(fill="x", pady=2)
            
            # วันที่
            ctk.CTkLabel(
                row,
                text=movement['created_at'],
                font=FONTS["small"],
                width=140
            ).pack(side="left", padx=5, pady=8)
            
            # ประเภท
            if movement['movement_type'] == 'in':
                type_text = "➕ เพิ่ม"
                type_color = COLORS["success"]
            else:
                type_text = "➖ ลด"
                type_color = COLORS["danger"]
            
            ctk.CTkLabel(
                row,
                text=type_text,
                font=FONTS["small"],
                width=140,
                text_color=type_color
            ).pack(side="left", padx=5)
            
            # จำนวน
            ctk.CTkLabel(
                row,
                text=str(movement['quantity']),
                font=("Sarabun", 13, "bold"),
                width=140
            ).pack(side="left", padx=5)
            
            # อ้างอิง
            ref_type = {
                'sale': 'ขาย',
                'return': 'คืน',
                'manual_adjustment': 'ปรับสต็อก',
                'initial': 'สต็อกเริ่มต้น'
            }.get(movement['reference_type'], movement['reference_type'])
            
            ctk.CTkLabel(
                row,
                text=ref_type,
                font=FONTS["small"],
                width=140
            ).pack(side="left", padx=5)
            
            # ผู้ดำเนินการ
            ctk.CTkLabel(
                row,
                text=movement['full_name'] or '-',
                font=FONTS["small"],
                width=140
            ).pack(side="left", padx=5)
            
            # หมายเหตุ
            ctk.CTkLabel(
                row,
                text=movement['notes'] or '-',
                font=FONTS["small"],
                width=140,
                anchor="w"
            ).pack(side="left", padx=5)
        
        # ปุ่มปิด
        ctk.CTkButton(
            dialog,
            text="ปิด",
            font=FONTS["button"],
            width=150,
            height=40,
            command=dialog.destroy
        ).pack(pady=(0, 20))
