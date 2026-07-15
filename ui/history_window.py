# -*- coding: utf-8 -*-
"""
หน้าประวัติการขาย — แสดงรายการวันนี้จากฐานข้อมูล
- แสดงเฉพาะวันนี้ (รีเซ็ตทุกวัน ไม่บวม)
- ยกเลิกบิล (void) + คืน stock
- ลบบิล
- ดูรายละเอียด + พิมพ์ใบเสร็จ
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
from datetime import datetime


class SalesHistoryFrame(ctk.CTkFrame):
    """Frame สำหรับดูประวัติการขายวันนี้ (ข้อมูลปัจจุบันจาก DB)"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        
        self.create_widgets()
        self.load_sales_history()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        today_str = datetime.now().strftime("%d/%m/%Y")
        title = ctk.CTkLabel(
            header_frame,
            text=f"📋 ประวัติการขายวันนี้ ({today_str})",
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
            command=self.load_sales_history
        )
        refresh_btn.pack(side="left", padx=5)
        
        # ค้นหาเลขที่ใบเสร็จ
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍 ค้นหาเลขที่ใบเสร็จ:",
            font=FONTS["body"]
        ).pack(side="left", padx=20, pady=15)
        
        self.search_number_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="SL...",
            font=FONTS["body"],
            width=200,
            height=35
        )
        self.search_number_entry.pack(side="left", padx=5)
        self.search_number_entry.bind("<Return>", lambda e: self.load_sales_history())
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="ค้นหา",
            font=FONTS["button"],
            width=100,
            height=40,
            fg_color=COLORS["primary"],
            command=self.load_sales_history
        )
        search_btn.pack(side="left", padx=10, pady=15)
        
        info_label = ctk.CTkLabel(
            search_frame,
            text="💡 ดูรายงานย้อนหลังและ Export ได้ที่ 📊 รายงานยอดขาย",
            font=FONTS["small"],
            text_color=COLORS["text_light"]
        )
        info_label.pack(side="right", padx=20)
        
        # สถิติสรุป
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.total_sales_card = self.create_stat_card(
            stats_frame, "💰 ยอดขายวันนี้", "฿0.00", COLORS["success"]
        )
        self.total_sales_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.total_count_card = self.create_stat_card(
            stats_frame, "📝 จำนวนรายการ", "0", COLORS["info"]
        )
        self.total_count_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.avg_sale_card = self.create_stat_card(
            stats_frame, "📊 ยอดเฉลี่ย", "฿0.00", COLORS["warning"]
        )
        self.avg_sale_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.void_count_card = self.create_stat_card(
            stats_frame, "🚫 ยกเลิก", "0", COLORS["danger"]
        )
        self.void_count_card.pack(side="left", fill="x", expand=True, padx=5)
        
        # ตารางรายการ
        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Header ตาราง
        header_row = ctk.CTkFrame(table_frame, fg_color=COLORS["primary"])
        header_row.pack(fill="x")
        
        headers = [
            ("เลขที่", 130),
            ("เวลา", 80),
            ("จำนวน", 60),
            ("ยอดรวม", 100),
            ("ส่วนลด", 80),
            ("ยอดสุทธิ", 110),
            ("พนักงาน", 100),
            ("สถานะ", 100),
            ("รายการสินค้า", 250),
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
            label.pack(side="left", padx=3, pady=10)
        
        # รายการ
        self.sales_container = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="white"
        )
        self.sales_container.pack(fill="both", expand=True)
        
    def create_stat_card(self, parent, title, value, color):
        """สร้างการ์ดสถิติ"""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=FONTS["small"],
            text_color="white"
        )
        title_label.pack(pady=(12, 3))
        
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Sarabun", 22, "bold"),
            text_color="white"
        )
        value_label.pack(pady=(0, 12))
        
        card.value_label = value_label
        return card
    
    def load_sales_history(self):
        """โหลดประวัติการขายวันนี้จาก DB"""
        # ล้างรายการเดิม
        for widget in self.sales_container.winfo_children():
            widget.destroy()
        
        # ดึงข้อมูลเฉพาะวันนี้
        today = datetime.now().strftime("%Y-%m-%d")
        
        params = [f"{today} 00:00:00", f"{today} 23:59:59"]
        search_query = ""
        
        sale_number = self.search_number_entry.get().strip()
        if sale_number:
            search_query = " AND s.sale_number LIKE ?"
            params.append(f"%{sale_number}%")
            
        limit = PERFORMANCE_MODE["items_per_page"] * 2 if PERFORMANCE_MODE["enabled"] else 200
        params.append(limit)
        
        self.db.connect()
        sales = self.db.fetch_all(f"""
            SELECT s.*, u.full_name as cashier_name,
                   COUNT(si.item_id) as item_count,
                   GROUP_CONCAT(COALESCE(si.product_name, 'Unknown') || ' x' || COALESCE(si.quantity, 0), ', ') as items_list
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE s.sale_date >= ? AND s.sale_date <= ? {search_query}
            GROUP BY s.sale_id
            ORDER BY s.sale_date DESC
            LIMIT ?
        """, tuple(params))
        self.db.disconnect()
        
        # คำนวณสถิติ
        active_sales = [s for s in sales if s['status'] == 'completed']
        voided_sales = [s for s in sales if s['status'] in ('voided', 'returned')]
        
        total_amount = sum(s['total_amount'] for s in active_sales)
        total_count = len(active_sales)
        avg_amount = total_amount / total_count if total_count > 0 else 0
        void_count = len(voided_sales)
        
        # อัพเดทสถิติ
        self.total_sales_card.value_label.configure(text=f"฿{total_amount:,.2f}")
        self.total_count_card.value_label.configure(text=f"{total_count:,}")
        self.avg_sale_card.value_label.configure(text=f"฿{avg_amount:,.2f}")
        self.void_count_card.value_label.configure(text=f"{void_count:,}")
        
        if not sales:
            no_data = ctk.CTkLabel(
                self.sales_container,
                text="ยังไม่มีรายการขายวันนี้\n(ข้อมูลจะปรากฏหลังทำการขาย)",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            )
            no_data.pack(pady=50)
            return
        
        # แสดงรายการ
        for idx, sale in enumerate(sales):
            self.create_sale_row(sale, idx)
    
    def create_sale_row(self, sale, index):
        """สร้างแถวรายการขาย"""
        is_voided = sale['status'] in ('voided', 'returned')
        
        if is_voided:
            bg_color = "#fff0f0"  # แดงอ่อนสำหรับรายการที่ยกเลิก
        else:
            bg_color = COLORS["light"] if index % 2 == 0 else "white"
        
        row = ctk.CTkFrame(self.sales_container, fg_color=bg_color, height=60)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # เลขที่
        ctk.CTkLabel(
            row,
            text=sale['sale_number'],
            font=FONTS["body"],
            width=130,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # เวลา
        try:
            sale_datetime = datetime.strptime(sale['sale_date'], DB_DATETIME_FORMAT)
            time_str = sale_datetime.strftime("%H:%M")
        except:
            time_str = "-"
        ctk.CTkLabel(
            row,
            text=time_str,
            font=FONTS["body"],
            width=80,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # จำนวนรายการ
        ctk.CTkLabel(
            row,
            text=str(sale['item_count']),
            font=FONTS["body"],
            width=60,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # ยอดรวม
        ctk.CTkLabel(
            row,
            text=f"฿{sale['subtotal']:,.2f}",
            font=FONTS["body"],
            width=100,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # ส่วนลด
        ctk.CTkLabel(
            row,
            text=f"฿{sale['discount_amount']:,.2f}",
            font=FONTS["body"],
            width=80,
            text_color="#ccc" if is_voided else COLORS["danger"]
        ).pack(side="left", padx=3)
        
        # ยอดสุทธิ
        if is_voided:
            total_text = f"ยกเลิก"
            total_color = COLORS["danger"]
        else:
            total_text = f"฿{sale['total_amount']:,.2f}"
            total_color = COLORS["success"]
            
        ctk.CTkLabel(
            row,
            text=total_text,
            font=("Sarabun", 13, "bold"),
            width=110,
            text_color=total_color
        ).pack(side="left", padx=3)
        
        # พนักงาน
        ctk.CTkLabel(
            row,
            text=sale['cashier_name'] or "-",
            font=FONTS["small"],
            width=100,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # สถานะ
        status_map = {
            'completed': ("✅ ปกติ", COLORS["success"]),
            'voided': ("🚫 ยกเลิก", COLORS["danger"]),
            'returned': ("↩️ คืน", COLORS["warning"]),
            'partially_returned': ("↩️ คืนบางส่วน", COLORS["warning"]),
        }
        status_text, status_color = status_map.get(sale['status'], ("?", "#999"))
        ctk.CTkLabel(
            row,
            text=status_text,
            font=FONTS["small"],
            width=100,
            text_color=status_color
        ).pack(side="left", padx=3)
        
        # รายการสินค้า (Summary)
        ctk.CTkLabel(
            row,
            text=sale['items_list'] or "-",
            font=FONTS["small"],
            width=250,
            anchor="w",
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # ปุ่มจัดการ
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=200)
        btn_frame.pack(side="left", padx=3)
        btn_frame.pack_propagate(False)
        
        # ดูรายละเอียด
        ctk.CTkButton(
            btn_frame,
            text="👁️",
            font=("Arial", 14),
            width=35,
            height=30,
            fg_color=COLORS["info"],
            command=lambda s=sale: self.view_sale_detail(s)
        ).pack(side="left", padx=2)
        
        # พิมพ์ใบเสร็จ
        ctk.CTkButton(
            btn_frame,
            text="🖨️",
            font=("Arial", 14),
            width=35,
            height=30,
            fg_color=COLORS["secondary"],
            command=lambda s=sale: self.print_receipt(s)
        ).pack(side="left", padx=2)
        
        # ยกเลิกบิล (เฉพาะบิลที่ completed เท่านั้น)
        if not is_voided:
            ctk.CTkButton(
                btn_frame,
                text="🚫",
                font=("Arial", 14),
                width=35,
                height=30,
                fg_color=COLORS["warning"],
                hover_color=COLORS["danger"],
                command=lambda s=sale: self.void_sale(s)
            ).pack(side="left", padx=2)
        
        # ลบบิล
        ctk.CTkButton(
            btn_frame,
            text="🗑️",
            font=("Arial", 14),
            width=35,
            height=30,
            fg_color=COLORS["danger"],
            command=lambda s_id=sale['sale_id']: self.delete_single_sale(s_id)
        ).pack(side="left", padx=2)
    
    # ==========================================================
    # ยกเลิกบิล (Void) — คืน stock + เปลี่ยนสถานะ + บันทึกลง backup
    # ==========================================================
    def void_sale(self, sale):
        """ยกเลิกบิล — คืน stock กลับอัตโนมัติ"""
        result = messagebox.askyesno(
            "ยืนยันยกเลิกบิล",
            f"ต้องการยกเลิกบิล {sale['sale_number']} หรือไม่?\n\n"
            f"ยอดเงิน: ฿{sale['total_amount']:,.2f}\n\n"
            f"⚠️ สินค้าจะถูกคืนกลับสต็อกอัตโนมัติ\n"
            f"⚠️ บันทึกการยกเลิกลงไฟล์ backup ด้วย"
        )
        
        if not result:
            return
        
        try:
            self.db.connect()
            self.db.begin_transaction()
            
            # 1. ดึงรายการสินค้าในบิลที่จะยกเลิก
            items = self.db.fetch_all(
                "SELECT product_id, quantity FROM sale_items WHERE sale_id = ?",
                (sale['sale_id'],)
            )
            
            # 2. คืน stock ทุกรายการ
            for item in items:
                self.db.execute("""
                    UPDATE products 
                    SET stock_quantity = stock_quantity + ?
                    WHERE product_id = ?
                """, (item['quantity'], item['product_id']))
                
                # บันทึกการเคลื่อนไหวสต็อก (คืน)
                self.db.execute("""
                    INSERT INTO stock_movements (
                        product_id, movement_type, quantity,
                        reference_id, reference_type, user_id, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item['product_id'], 'in', item['quantity'],
                    sale['sale_id'], 'void', self.user_id,
                    f"ยกเลิกบิล {sale['sale_number']}"
                ))
            
            # 3. เปลี่ยนสถานะบิลเป็น voided
            self.db.execute(
                "UPDATE sales SET status = 'voided' WHERE sale_id = ?",
                (sale['sale_id'],)
            )
            
            # ทุกอย่างสำเร็จ — commit
            self.db.commit_transaction()
            self.db.disconnect()
            
            # 4. บันทึกลง backup .txt
            try:
                from utils import SalesLogManager
                slm = SalesLogManager()
                slm.add_sale({
                    "sale_number": f"VOID-{sale['sale_number']}",
                    "total_amount": -sale['total_amount'],
                    "payment_method": "void"
                })
            except Exception as e:
                print(f"[WARN] Could not log void to backup: {e}")
            
            messagebox.showinfo(
                "สำเร็จ",
                f"ยกเลิกบิล {sale['sale_number']} เรียบร้อย\n"
                f"คืนสินค้า {len(items)} รายการกลับสต็อกแล้ว"
            )
            
            self.load_sales_history()
            
        except Exception as e:
            self.db.rollback_transaction()
            self.db.disconnect()
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถยกเลิกบิลได้:\n{e}")
    
    # ==========================================================
    # ดูรายละเอียด
    # ==========================================================
    def view_sale_detail(self, sale):
        """ดูรายละเอียดการขาย"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"รายละเอียด - {sale['sale_number']}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        
        is_voided = sale['status'] in ('voided', 'returned')
        
        # ข้อมูลหลัก
        info_frame = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        status_text = "🚫 ยกเลิกแล้ว" if is_voided else "✅ ปกติ"
        
        info_text = f"""
        เลขที่: {sale['sale_number']}
        วันที่/เวลา: {sale['sale_date']}
        ประเภทราคา: {PRICE_TYPES.get(sale['price_type'], '-')}
        พนักงานขาย: {sale.get('cashier_name', '-')}
        สถานะ: {status_text}
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
        
        items_frame = ctk.CTkScrollableFrame(dialog, fg_color="white", corner_radius=10, height=250)
        items_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.db.connect()
        items = self.db.fetch_all(
            "SELECT * FROM sale_items WHERE sale_id = ?",
            (sale['sale_id'],)
        )
        self.db.disconnect()
        
        for item in items:
            item_row = ctk.CTkFrame(items_frame, fg_color=COLORS["light"], corner_radius=5)
            item_row.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(item_row, text=item['product_name'], font=FONTS["body"], anchor="w").pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(item_row, text=f"{item['quantity']} x ฿{item['unit_price']:,.2f}", font=FONTS["body"]).pack(side="left", padx=10)
            ctk.CTkLabel(item_row, text=f"฿{item['total_price']:,.2f}", font=("Sarabun", 14, "bold"), text_color=COLORS["success"]).pack(side="right", padx=10)
        
        # สรุปยอด
        summary_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        summary_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        for label, value in [
            ("ยอดรวม:", f"฿{sale['subtotal']:,.2f}"),
            ("ส่วนลด:", f"฿{sale['discount_amount']:,.2f}"),
            ("ภาษี VAT:", f"฿{sale['tax_amount']:,.2f}"),
            ("ยอดสุทธิ:", f"฿{sale['total_amount']:,.2f}"),
            ("รับเงิน:", f"฿{sale['paid_amount']:,.2f}"),
            ("เงินทอน:", f"฿{sale['change_amount']:,.2f}"),
        ]:
            row = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=label, font=FONTS["body"]).pack(side="left")
            ctk.CTkLabel(row, text=value, font=FONTS["body"],
                        text_color=COLORS["success"] if "ยอดสุทธิ" in label else COLORS["text_dark"]).pack(side="right")
        
        ctk.CTkButton(dialog, text="ปิด", font=FONTS["button"], width=150, height=40, command=dialog.destroy).pack(pady=(0, 20))
    
    # ==========================================================
    # พิมพ์ใบเสร็จ
    # ==========================================================
    def print_receipt(self, sale):
        """พิมพ์ใบเสร็จ"""
        self.db.connect()
        items = self.db.fetch_all("SELECT * FROM sale_items WHERE sale_id = ?", (sale['sale_id'],))
        self.db.disconnect()
        
        receipt_data = {
            'company': COMPANY_INFO,
            'sale_number': sale['sale_number'],
            'sale_date': sale['sale_date'],
            'customer_name': sale.get('customer_name') or 'ลูกค้าทั่วไป',
            'cashier': sale.get('cashier_name', '-'),
            'items': [dict(item) for item in items],
            'subtotal': sale['subtotal'],
            'discount_amount': sale['discount_amount'],
            'tax_amount': sale['tax_amount'],
            'total_amount': sale['total_amount'],
            'paid_amount': sale['paid_amount'],
            'change_amount': sale['change_amount']
        }
        
        try:
            from utils import print_receipt
            if print_receipt(receipt_data):
                messagebox.showinfo("สำเร็จ", "พิมพ์ใบเสร็จสำเร็จ!")
            else:
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถพิมพ์ใบเสร็จได้")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด:\n{e}")

    # ==========================================================
    # ลบบิล
    # ==========================================================
    def delete_single_sale(self, sale_id):
        """ลบรายการขายเดียว (คืน stock ก่อนลบ)"""
        if messagebox.askyesno("ยืนยันการลบ", "คุณต้องการลบรายการขายนี้ใช่หรือไม่?\n⚠️ ข้อมูลจะหายถาวร (แต่ backup .txt ยังอยู่)\n📦 สต็อกจะถูกคืนกลับอัตโนมัติ"):
            self.db.connect()
            self.db.begin_transaction()
            
            try:
                # คืน stock ก่อนลบ (BUG-021)
                items = self.db.fetch_all(
                    "SELECT product_id, quantity FROM sale_items WHERE sale_id = ?",
                    (sale_id,)
                )
                
                for item in items:
                    self.db.execute("""
                        UPDATE products 
                        SET stock_quantity = stock_quantity + ?
                        WHERE product_id = ?
                    """, (item['quantity'], item['product_id']))
                
                # ลบ sale_items แล้วค่อยลบ sales
                self.db.execute("DELETE FROM sale_items WHERE sale_id = ?", (sale_id,))
                success = self.db.execute("DELETE FROM sales WHERE sale_id = ?", (sale_id,))
                
                if not success:
                    raise Exception("ไม่สามารถลบข้อมูลได้")
                
                self.db.commit_transaction()
                self.db.disconnect()
                
                messagebox.showinfo("สำเร็จ", f"ลบรายการขายเรียบร้อย\n📦 คืนสินค้า {len(items)} รายการกลับสต็อกแล้ว")
                self.load_sales_history()
            except Exception as e:
                self.db.rollback_transaction()
                self.db.disconnect()
                messagebox.showerror("ผิดพลาด", f"ไม่สามารถลบข้อมูลได้:\n{e}")
