# -*- coding: utf-8 -*-
"""
หน้าการขายที่พัก (Parked Sales)
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
import json


class ParkedSalesFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการการขายที่พัก"""
    
    def __init__(self, parent, user_id, on_load_callback=None):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        self.on_load_callback = on_load_callback  # callback สำหรับโหลดกลับไปหน้า POS
        
        self.create_widgets()
        self.load_parked_sales()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text="💾 การขายที่พัก",
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
            command=self.load_parked_sales
        )
        refresh_btn.pack(side="right")
        
        # คำอธิบาย
        desc = ctk.CTkLabel(
            self,
            text="รายการที่พักไว้สามารถกลับมาขายต่อได้ในภายหลัง",
            font=FONTS["body"],
            text_color=COLORS["text_light"]
        )
        desc.pack(padx=20, pady=(0, 15))
        
        # รายการ
        self.parked_container = ctk.CTkScrollableFrame(
            self,
            fg_color="white",
            corner_radius=10
        )
        self.parked_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def load_parked_sales(self):
        """โหลดรายการที่พัก"""
        # ล้างรายการเดิม
        for widget in self.parked_container.winfo_children():
            widget.destroy()
        
        # ดึงข้อมูล
        self.db.connect()
        parked_sales = self.db.fetch_all("""
            SELECT ps.*, u.full_name as user_name
            FROM parked_sales ps
            LEFT JOIN users u ON ps.user_id = u.user_id
            ORDER BY ps.parked_id DESC
        """)
        self.db.disconnect()
        
        if not parked_sales:
            no_data = ctk.CTkLabel(
                self.parked_container,
                text="ไม่มีรายการที่พัก",
                font=FONTS["heading"],
                text_color=COLORS["text_light"]
            )
            no_data.pack(pady=50)
            return
        
        # แสดงรายการ
        for parked in parked_sales:
            self.create_parked_card(parked)
    
    def create_parked_card(self, parked):
        """สร้างการ์ดรายการพัก"""
        card = ctk.CTkFrame(
            self.parked_container,
            fg_color=COLORS["light"],
            corner_radius=10
        )
        card.pack(fill="x", padx=10, pady=10)
        
        # ส่วนซ้าย: ข้อมูล
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        
        # หัวข้อ
        header_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header_row,
            text=f"🏷️ {parked['parked_name']}",
            font=FONTS["heading"],
            text_color=COLORS["primary"],
            anchor="w"
        ).pack(side="left")
        
        # รายละเอียด
        detail_text = f"""
        📅 วันที่พัก: {parked['parked_date']}
        👤 พนักงาน: {parked['user_name']}
        💰 ยอดรวม: ฿{parked['total_amount']:,.2f}
        📝 หมายเหตุ: {parked['notes'] or '-'}
        """
        
        ctk.CTkLabel(
            info_frame,
            text=detail_text,
            font=FONTS["body"],
            text_color=COLORS["text_dark"],
            justify="left",
            anchor="w"
        ).pack(fill="x")
        
        # รายการสินค้า
        try:
            items = json.loads(parked['cart_items'])
            items_text = f"🛒 จำนวนสินค้า: {len(items)} รายการ"
            
            ctk.CTkLabel(
                info_frame,
                text=items_text,
                font=("Sarabun", 13, "bold"),
                text_color=COLORS["info"]
            ).pack(pady=(5, 0))
        except:
            pass
        
        # ส่วนขวา: ปุ่ม
        btn_frame = ctk.CTkFrame(card, fg_color="transparent", width=200)
        btn_frame.pack(side="right", padx=20, pady=15)
        btn_frame.pack_propagate(False)
        
        # ปุ่มดูรายละเอียด
        view_btn = ctk.CTkButton(
            btn_frame,
            text="👁️ ดูรายละเอียด",
            font=FONTS["button"],
            height=45,
            fg_color=COLORS["info"],
            command=lambda p=parked: self.view_details(p)
        )
        view_btn.pack(fill="x", pady=5)
        
        # ปุ่มโหลด
        load_btn = ctk.CTkButton(
            btn_frame,
            text="▶️ โหลดกลับไปขาย",
            font=FONTS["button"],
            height=45,
            fg_color=COLORS["success"],
            command=lambda p=parked: self.load_parked_sale(p)
        )
        load_btn.pack(fill="x", pady=5)
        
        # ปุ่มลบ
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="🗑️ ลบ",
            font=FONTS["button"],
            height=45,
            fg_color=COLORS["danger"],
            command=lambda p=parked: self.delete_parked_sale(p)
        )
        delete_btn.pack(fill="x", pady=5)
    
    def view_details(self, parked):
        """ดูรายละเอียด"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"รายละเอียด - {parked['parked_name']}")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # ข้อมูลหลัก
        info_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        info_text = f"""
        ชื่อ: {parked['parked_name']}
        วันที่/เวลา: {parked['parked_date']}
        พนักงาน: {parked['user_name']}
        ลูกค้า: {parked['customer_name'] or 'ลูกค้าทั่วไป'}
        ประเภทราคา: {PRICE_TYPES.get(parked['price_type'], '-')}
        หมายเหตุ: {parked['notes'] or '-'}
        """
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=FONTS["body"],
            justify="left"
        ).pack(padx=20, pady=20)
        
        # รายการสินค้า
        ctk.CTkLabel(
            dialog,
            text="รายการสินค้า",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(pady=(0, 10))
        
        items_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color="white",
            corner_radius=10,
            height=200
        )
        items_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        try:
            items = json.loads(parked['cart_items'])
            
            for item in items:
                item_row = ctk.CTkFrame(items_frame, fg_color=COLORS["light"], corner_radius=5)
                item_row.pack(fill="x", padx=5, pady=5)
                
                ctk.CTkLabel(
                    item_row,
                    text=item['name'],
                    font=FONTS["body"],
                    anchor="w"
                ).pack(side="left", padx=10, pady=10)
                
                ctk.CTkLabel(
                    item_row,
                    text=f"{item['quantity']} x ฿{item['price']:,.2f}",
                    font=FONTS["body"]
                ).pack(side="left", padx=10)
                
                ctk.CTkLabel(
                    item_row,
                    text=f"฿{item['total']:,.2f}",
                    font=("Sarabun", 14, "bold"),
                    text_color=COLORS["success"]
                ).pack(side="right", padx=10)
        except Exception as e:
            ctk.CTkLabel(
                items_frame,
                text=f"ไม่สามารถแสดงรายการได้: {e}",
                font=FONTS["body"],
                text_color=COLORS["danger"]
            ).pack(pady=20)
        
        # สรุปยอด
        summary_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        summary_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        summary_row = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_row.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            summary_row,
            text="ยอดรวมทั้งหมด:",
            font=("Sarabun", 16, "bold")
        ).pack(side="left")
        
        ctk.CTkLabel(
            summary_row,
            text=f"฿{parked['total_amount']:,.2f}",
            font=("Sarabun", 20, "bold"),
            text_color=COLORS["success"]
        ).pack(side="right")
        
        # ปุ่มปิด
        ctk.CTkButton(
            dialog,
            text="ปิด",
            font=FONTS["button"],
            width=150,
            height=40,
            command=dialog.destroy
        ).pack(pady=(0, 20))
    
    def load_parked_sale(self, parked):
        """โหลดการขายกลับไปหน้า POS"""
        result = messagebox.askyesno(
            "ยืนยัน",
            f"ต้องการโหลด '{parked['parked_name']}' กลับไปขายต่อหรือไม่?"
        )
        
        if not result:
            return
        
        # ส่งข้อมูลกลับผ่าน callback
        if self.on_load_callback:
            try:
                items = json.loads(parked['cart_items'])
                cart_data = {
                    'items': items,
                    'customer_name': parked['customer_name'],
                    'price_type': parked['price_type'],
                    'discount_type': parked['discount_type'],
                    'discount_value': parked['discount_value']
                }
                
                self.on_load_callback(cart_data)
                
                # ลบรายการที่พัก
                self.db.connect()
                self.db.execute(
                    "DELETE FROM parked_sales WHERE parked_id = ?",
                    (parked['parked_id'],)
                )
                self.db.disconnect()
                
                messagebox.showinfo("สำเร็จ", "โหลดการขายสำเร็จ!")
                self.load_parked_sales()  # รีเฟรชรายการ
                
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดข้อมูลได้: {e}")
        else:
            messagebox.showwarning(
                "แจ้งเตือน",
                "กรุณากลับไปหน้าขายเพื่อโหลดการขายที่พัก"
            )
    
    def delete_parked_sale(self, parked):
        """ลบการขายที่พัก"""
        result = messagebox.askyesno(
            "ยืนยันการลบ",
            f"ต้องการลบ '{parked['parked_name']}' หรือไม่?\n\nการลบจะไม่สามารถกู้คืนได้"
        )
        
        if not result:
            return
        
        self.db.connect()
        success = self.db.execute(
            "DELETE FROM parked_sales WHERE parked_id = ?",
            (parked['parked_id'],)
        )
        self.db.disconnect()
        
        if success:
            messagebox.showinfo("สำเร็จ", "ลบการขายที่พักสำเร็จ")
            self.load_parked_sales()
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถลบได้")
