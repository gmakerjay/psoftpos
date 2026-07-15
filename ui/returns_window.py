# -*- coding: utf-8 -*-
"""
หน้าคืนสินค้า
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
from datetime import datetime


class ReturnsFrame(ctk.CTkFrame):
    """Frame สำหรับคืนสินค้า"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        self.selected_sale = None
        self.return_items = []
        
        self.create_widgets()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        title = ctk.CTkLabel(
            self,
            text="↩️ คืนสินค้า",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(padx=20, pady=20, anchor="w")
        
        # แบ่ง 2 ส่วน
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=(0, 20))
        
        right_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=15, width=400)
        right_frame.pack(side="right", fill="y", padx=(10, 20), pady=(0, 20))
        right_frame.pack_propagate(False)
        
        # ซ้าย: ค้นหาใบเสร็จ
        self.create_search_panel(left_frame)
        
        # ขวา: รายการคืน
        self.create_return_panel(right_frame)
    
    def create_search_panel(self, parent):
        """สร้างแผงค้นหา"""
        # ค้นหา
        search_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍 ค้นหาใบเสร็จ:",
            font=FONTS["body"]
        ).pack(side="left", padx=15, pady=15)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="กรอกเลขที่ใบเสร็จ...",
            font=FONTS["body"],
            height=40,
            width=250
        )
        self.search_entry.pack(side="left", padx=10, pady=15)
        self.search_entry.bind("<Return>", lambda e: self.search_sale())
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="ค้นหา",
            font=FONTS["button"],
            width=100,
            height=40,
            fg_color=COLORS["primary"],
            command=self.search_sale
        )
        search_btn.pack(side="left", padx=(0, 15), pady=15)
        
        # ข้อมูลใบเสร็จ
        self.sale_info_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        self.sale_info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            self.sale_info_frame,
            text="กรุณาค้นหาใบเสร็จก่อน",
            font=FONTS["body"],
            text_color=COLORS["text_light"]
        ).pack(pady=30)
        
        # รายการสินค้าในใบเสร็จ
        ctk.CTkLabel(
            parent,
            text="รายการสินค้า",
            font=FONTS["heading"],
            text_color=COLORS["text_dark"]
        ).pack(pady=(0, 10), anchor="w")
        
        self.items_container = ctk.CTkScrollableFrame(
            parent,
            fg_color="white",
            corner_radius=10
        )
        self.items_container.pack(fill="both", expand=True)
        
    def create_return_panel(self, parent):
        """สร้างแผงรายการคืน"""
        # Header
        header = ctk.CTkFrame(parent, fg_color=COLORS["danger"])
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text="รายการสินค้าที่คืน",
            font=FONTS["heading"],
            text_color="white"
        ).pack(pady=15)
        
        # รายการ
        self.return_list = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS["light"],
            height=300
        )
        self.return_list.pack(fill="both", expand=True)
        
        # เหตุผล
        ctk.CTkLabel(
            parent,
            text="เหตุผลการคืน:",
            font=FONTS["body"]
        ).pack(padx=15, pady=(15, 5), anchor="w")
        
        self.reason_entry = ctk.CTkTextbox(
            parent,
            font=FONTS["body"],
            height=80
        )
        self.reason_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # สรุป
        summary_frame = ctk.CTkFrame(parent, fg_color=COLORS["light"], corner_radius=10)
        summary_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        sum_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        sum_row.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            sum_row,
            text="ยอดคืน:",
            font=("Sarabun", 18, "bold")
        ).pack(side="left")
        
        self.return_total_label = ctk.CTkLabel(
            sum_row,
            text="฿0.00",
            font=("Sarabun", 20, "bold"),
            text_color=COLORS["danger"]
        )
        self.return_total_label.pack(side="right")
        
        # ปุ่ม
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="ล้างรายการ",
            font=FONTS["button"],
            height=45,
            fg_color=COLORS["text_light"],
            command=self.clear_return_list
        )
        clear_btn.pack(fill="x", pady=5)
        
        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="ยืนยันคืนสินค้า",
            font=("Sarabun", 16, "bold"),
            height=60,
            fg_color=COLORS["danger"],
            hover_color="#cc0000",
            command=self.process_return
        )
        confirm_btn.pack(fill="x", pady=5)
    
    def search_sale(self):
        """ค้นหาใบเสร็จ"""
        sale_number = self.search_entry.get().strip()
        
        if not sale_number:
            messagebox.showwarning("แจ้งเตือน", "กรุณากรอกเลขที่ใบเสร็จ")
            return
        
        # ค้นหา
        self.db.connect()
        sale = self.db.fetch_one("""
            SELECT s.*, u.full_name as cashier_name
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE s.sale_number = ? AND s.status = 'completed'
        """, (sale_number,))
        
        if not sale:
            self.db.disconnect()
            messagebox.showerror("ไม่พบข้อมูล", f"ไม่พบใบเสร็จเลขที่: {sale_number}")
            return
        
        # ดึงรายการสินค้า
        items = self.db.fetch_all(
            "SELECT * FROM sale_items WHERE sale_id = ?",
            (sale['sale_id'],)
        )
        self.db.disconnect()
        
        # เก็บข้อมูล
        self.selected_sale = sale
        self.selected_sale['items'] = items
        
        # แสดงข้อมูล
        self.display_sale_info()
        self.display_sale_items()
    
    def display_sale_info(self):
        """แสดงข้อมูลใบเสร็จ"""
        # ล้างข้อมูลเดิม
        for widget in self.sale_info_frame.winfo_children():
            widget.destroy()
        
        sale = self.selected_sale
        
        info_text = f"""
เลขที่: {sale['sale_number']}
วันที่: {sale['sale_date']}
ลูกค้า: {sale['customer_name'] or 'ลูกค้าทั่วไป'}
พนักงาน: {sale['cashier_name']}
ยอดสุทธิ: ฿{sale['total_amount']:,.2f}
        """
        
        ctk.CTkLabel(
            self.sale_info_frame,
            text=info_text,
            font=FONTS["body"],
            justify="left"
        ).pack(padx=20, pady=20)
    
    def display_sale_items(self):
        """แสดงรายการสินค้า"""
        # ล้างรายการเดิม
        for widget in self.items_container.winfo_children():
            widget.destroy()
        
        items = self.selected_sale['items']
        
        for item in items:
            item_frame = ctk.CTkFrame(
                self.items_container,
                fg_color=COLORS["light"],
                corner_radius=8
            )
            item_frame.pack(fill="x", padx=5, pady=5)
            
            # ชื่อสินค้า
            info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text=item['product_name'],
                font=FONTS["body"],
                anchor="w"
            ).pack(fill="x")
            
            ctk.CTkLabel(
                info_frame,
                text=f"{item['quantity']} x ฿{item['unit_price']:,.2f} = ฿{item['total_price']:,.2f}",
                font=FONTS["small"],
                text_color=COLORS["text_light"],
                anchor="w"
            ).pack(fill="x")
            
            # ปุ่มคืน
            return_btn = ctk.CTkButton(
                item_frame,
                text="↩️ คืน",
                font=FONTS["button"],
                width=80,
                height=40,
                fg_color=COLORS["danger"],
                command=lambda i=item: self.add_to_return_list(i)
            )
            return_btn.pack(side="right", padx=10, pady=10)
    
    def add_to_return_list(self, item):
        """เพิ่มสินค้าในรายการคืน"""
        # ตรวจสอบว่ามีในรายการแล้วหรือไม่
        for return_item in self.return_items:
            if return_item['item_id'] == item['item_id']:
                messagebox.showwarning("แจ้งเตือน", "มีสินค้านี้ในรายการคืนแล้ว")
                return
        
        # เพิ่มรายการ
        self.return_items.append({
            'item_id': item['item_id'],
            'product_id': item['product_id'],
            'product_name': item['product_name'],
            'quantity': item['quantity'],
            'max_quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'total_price': item['total_price']
        })
        
        self.update_return_display()
    
    def update_return_display(self):
        """อัพเดทการแสดงผลรายการคืน"""
        # ล้างรายการเดิม
        for widget in self.return_list.winfo_children():
            widget.destroy()
        
        if not self.return_items:
            ctk.CTkLabel(
                self.return_list,
                text="ยังไม่มีสินค้าในรายการคืน",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            ).pack(pady=30)
            self.return_total_label.configure(text="฿0.00")
            return
        
        # แสดงรายการ
        for idx, item in enumerate(self.return_items):
            item_frame = ctk.CTkFrame(
                self.return_list,
                fg_color="white",
                corner_radius=8
            )
            item_frame.pack(fill="x", padx=5, pady=5)
            
            # ชื่อ
            ctk.CTkLabel(
                item_frame,
                text=item['product_name'],
                font=FONTS["body"],
                anchor="w"
            ).pack(fill="x", padx=10, pady=(10, 5))
            
            # จำนวน
            detail_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            detail_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # ปุ่มลด
            minus_btn = ctk.CTkButton(
                detail_frame,
                text="-",
                width=30,
                height=30,
                font=("Arial", 16, "bold"),
                fg_color=COLORS["text_light"],
                command=lambda i=idx: self.decrease_return_quantity(i)
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
                command=lambda i=idx: self.increase_return_quantity(i)
            )
            plus_btn.pack(side="left", padx=2)
            
            # ราคา
            total_label = ctk.CTkLabel(
                detail_frame,
                text=f"฿{item['total_price']:,.2f}",
                font=("Sarabun", 14, "bold"),
                text_color=COLORS["danger"]
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
                command=lambda i=idx: self.remove_from_return_list(i)
            )
            delete_btn.pack(side="right", padx=5)
        
        # อัพเดทยอดรวม
        total = sum(item['total_price'] for item in self.return_items)
        self.return_total_label.configure(text=f"฿{total:,.2f}")
    
    def increase_return_quantity(self, index):
        """เพิ่มจำนวนคืน"""
        item = self.return_items[index]
        if item['quantity'] < item['max_quantity']:
            item['quantity'] += 1
            item['total_price'] = item['quantity'] * item['unit_price']
            self.update_return_display()
    
    def decrease_return_quantity(self, index):
        """ลดจำนวนคืน"""
        item = self.return_items[index]
        if item['quantity'] > 1:
            item['quantity'] -= 1
            item['total_price'] = item['quantity'] * item['unit_price']
            self.update_return_display()
        else:
            self.remove_from_return_list(index)
    
    def remove_from_return_list(self, index):
        """ลบออกจากรายการคืน"""
        del self.return_items[index]
        self.update_return_display()
    
    def clear_return_list(self):
        """ล้างรายการคืน"""
        if self.return_items:
            result = messagebox.askyesno(
                "ยืนยัน",
                "ต้องการล้างรายการคืนทั้งหมดหรือไม่?"
            )
            if result:
                self.return_items = []
                self.update_return_display()
    
    def process_return(self):
        """ประมวลผลการคืนสินค้า"""
        if not self.selected_sale:
            messagebox.showwarning("แจ้งเตือน", "กรุณาค้นหาใบเสร็จก่อน")
            return
        
        if not self.return_items:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกสินค้าที่ต้องการคืน")
            return
        
        reason = self.reason_entry.get("1.0", "end").strip()
        
        # ยืนยัน
        total_return = sum(item['total_price'] for item in self.return_items)
        result = messagebox.askyesno(
            "ยืนยันการคืนสินค้า",
            f"ยอดคืน: ฿{total_return:,.2f}\n\nต้องการดำเนินการคืนสินค้าหรือไม่?"
        )
        
        if not result:
            return
        
        # บันทึกการคืน (ใช้ Transaction ป้องกันข้อมูลไม่สอดคล้อง)
        self.db.connect()
        self.db.begin_transaction()
        
        try:
            return_number = self.db.generate_return_number()
            return_date = datetime.now().strftime(DB_DATETIME_FORMAT)
            return_type = 'partial' if len(self.return_items) < len(self.selected_sale['items']) else 'full'
            
            # บันทึกข้อมูลหลัก
            success = self.db.execute("""
                INSERT INTO returns (
                    return_number, sale_id, return_date, user_id,
                    return_type, total_amount, reason, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                return_number, self.selected_sale['sale_id'], return_date,
                self.user_id, return_type, total_return, reason, 'completed'
            ))
            
            if not success:
                raise Exception("ไม่สามารถบันทึกการคืนสินค้าได้")
            
            # ดึง return_id
            ret = self.db.fetch_one(
                "SELECT return_id FROM returns WHERE return_number = ?",
                (return_number,)
            )
            return_id = ret['return_id']
            
            # บันทึกรายการสินค้าที่คืน
            for item in self.return_items:
                self.db.execute("""
                    INSERT INTO return_items (
                        return_id, product_id, quantity,
                        unit_price, total_price
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    return_id, item['product_id'], item['quantity'],
                    item['unit_price'], item['total_price']
                ))
                
                # เพิ่มสต็อกกลับ
                self.db.execute("""
                    UPDATE products
                    SET stock_quantity = stock_quantity + ?
                    WHERE product_id = ?
                """, (item['quantity'], item['product_id']))
                
                # บันทึกการเคลื่อนไหวสต็อก
                self.db.execute("""
                    INSERT INTO stock_movements (
                        product_id, movement_type, quantity,
                        reference_id, reference_type, user_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item['product_id'], 'in', item['quantity'],
                    return_id, 'return', self.user_id, f'คืนสินค้า {return_number}'
                ))
            
            # อัพเดทสถานะ sales หลังจากทุกอย่างสำเร็จ (แก้ BUG-004)
            sale_status = 'returned' if return_type == 'full' else 'partially_returned'
            self.db.execute(
                "UPDATE sales SET status = ? WHERE sale_id = ?",
                (sale_status, self.selected_sale['sale_id'])
            )
            
            # ทุกอย่างสำเร็จ — commit ทั้งหมด
            self.db.commit_transaction()
            self.db.disconnect()
        except Exception as e:
            # ล้มเหลว — rollback ทั้งหมด
            self.db.rollback_transaction()
            self.db.disconnect()
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการคืนสินค้าได้:\n{e}")
            return
        
        # แสดงข้อความสำเร็จ
        messagebox.showinfo(
            "สำเร็จ",
            f"คืนสินค้าสำเร็จ!\n\nเลขที่: {return_number}\nยอดคืน: ฿{total_return:,.2f}"
        )
        
        # ล้างข้อมูล
        self.selected_sale = None
        self.return_items = []
        self.search_entry.delete(0, 'end')
        self.reason_entry.delete("1.0", "end")
        
        # ล้าง UI
        for widget in self.sale_info_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(
            self.sale_info_frame,
            text="กรุณาค้นหาใบเสร็จก่อน",
            font=FONTS["body"],
            text_color=COLORS["text_light"]
        ).pack(pady=30)
        
        for widget in self.items_container.winfo_children():
            widget.destroy()
        
        self.update_return_display()
