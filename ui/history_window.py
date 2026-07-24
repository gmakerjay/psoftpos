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
from tkcalendar import DateEntry
from tkinter import filedialog
from utils import ExcelManager


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
        
        title = ctk.CTkLabel(
            header_frame,
            text="📋 ค้นหาบิลและประวัติการขาย",
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
        
        # ตัวกรองการค้นหา (วันที่ และ คำสำคัญ)
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # ส่วนเลือกวันที่
        date_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        date_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(date_frame, text="จากวันที่:", font=FONTS["body"]).pack(side="left")
        self.start_date = DateEntry(date_frame, width=11, background=COLORS["primary"], date_pattern='dd/mm/yyyy')
        self.start_date.pack(side="left", padx=5)
        
        ctk.CTkLabel(date_frame, text="ถึงวันที่:", font=FONTS["body"]).pack(side="left")
        self.end_date = DateEntry(date_frame, width=11, background=COLORS["primary"], date_pattern='dd/mm/yyyy')
        self.end_date.pack(side="left", padx=5)
        
        # ช่องค้นหาคำสำคัญ
        ctk.CTkLabel(
            search_frame,
            text="🔍 ค้นหา:",
            font=FONTS["body"]
        ).pack(side="left", padx=(10, 2), pady=15)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="เลขที่บิล/ชื่อลูกค้า/สมาชิก/พนักงาน/สินค้า",
            font=FONTS["body"],
            width=280,
            height=35
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.load_sales_history())
        
        search_btn = ctk.CTkButton(
            search_frame,
            text="ค้นหา",
            font=FONTS["button"],
            width=80,
            height=35,
            fg_color=COLORS["primary"],
            command=self.load_sales_history
        )
        search_btn.pack(side="left", padx=5, pady=15)
        
        # ปุ่มส่งออก Excel
        export_btn = ctk.CTkButton(
            search_frame,
            text="📥 Export Excel",
            font=FONTS["button"],
            width=120,
            height=35,
            fg_color=COLORS["success"],
            command=self.export_history_to_excel
        )
        export_btn.pack(side="right", padx=20, pady=15)
        
        # สถิติสรุป
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.total_sales_card = self.create_stat_card(
            stats_frame, "💰 ยอดรวมที่แสดง", "฿0.00", COLORS["success"]
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
            ("เลขที่", 115),
            ("เวลา/วันที่", 95),
            ("จำนวน", 45),
            ("ยอดรวม", 80),
            ("ส่วนลด", 65),
            ("ยอดสุทธิ", 90),
            ("พนักงาน", 85),
            ("สถานะ", 85),
        ]
        
        # ปุ่มจัดการชิดขวา (เว้นระยะขวา 22px สำหรับ Scrollbar เพื่อไม่ให้บังปุ่มลบ)
        ctk.CTkLabel(
            header_row,
            text="จัดการ",
            font=FONTS["button"],
            text_color="white",
            width=235
        ).pack(side="right", padx=(3, 22), pady=10)

        for header, width in headers:
            label = ctk.CTkLabel(
                header_row,
                text=header,
                font=FONTS["button"],
                text_color="white",
                width=width
            )
            label.pack(side="left", padx=3, pady=10)

        # รายการสินค้ายืดหยุ่น
        ctk.CTkLabel(
            header_row,
            text="รายการสินค้า",
            font=FONTS["button"],
            text_color="white",
            anchor="w"
        ).pack(side="left", fill="x", expand=True, padx=3, pady=10)
        
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
        """โหลดประวัติการขายตามตัวกรอง"""
        # ล้างรายการเดิม
        for widget in self.sales_container.winfo_children():
            widget.destroy()
        
        try:
            filter_start = self.start_date.get_date()
            filter_end = self.end_date.get_date()
            start_str = f"{filter_start.strftime('%Y-%m-%d')} 00:00:00"
            end_str = f"{filter_end.strftime('%Y-%m-%d')} 23:59:59"
        except:
            today = datetime.now().strftime("%Y-%m-%d")
            start_str = f"{today} 00:00:00"
            end_str = f"{today} 23:59:59"
        
        params = [start_str, end_str]
        search_query = ""
        
        keyword = self.search_entry.get().strip()
        if keyword:
            search_query = """ AND (
                s.sale_number LIKE ? 
                OR m.name LIKE ? 
                OR m.phone LIKE ? 
                OR u.full_name LIKE ? 
                OR si.product_name LIKE ?
            )"""
            params.extend([f"%{keyword}%"] * 5)
            
        limit = PERFORMANCE_MODE["items_per_page"] * 2 if PERFORMANCE_MODE["enabled"] else 200
        params.append(limit)
        
        self.db.connect()
        sales = self.db.fetch_all(f"""
            SELECT s.*, u.full_name as cashier_name,
                   COUNT(si.item_id) as item_count,
                   GROUP_CONCAT(COALESCE(si.product_name, 'Unknown') || ' x' || COALESCE(si.quantity, 0), ', ') as items_list,
                   m.name as member_name
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            LEFT JOIN members m ON s.member_id = m.member_id
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
                text="ไม่พบรายการขายตามเงื่อนไขการค้นหา",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            )
            no_data.pack(pady=50)
            return
        
        # แสดงรายการ
        for idx, sale in enumerate(sales):
            self.create_sale_row(sale, idx)
            
    def create_sale_row(self, sale, index):
        """สร้างแถวรายการขาย (Responsive: ปุ่มจัดการชิดขวาสุด รายการสินค้ายืดตามพื้นที่)"""
        is_voided = sale['status'] in ('voided', 'returned')
        
        if is_voided:
            bg_color = "#fff0f0"  # แดงอ่อนสำหรับรายการที่ยกเลิก
        else:
            bg_color = COLORS["light"] if index % 2 == 0 else "white"
        
        row = ctk.CTkFrame(self.sales_container, fg_color=bg_color, height=54)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # ปุ่มจัดการ (ตรึงชิดขวา พร้อมเว้นระยะขวา 22px หลบ Scrollbar เพื่อให้ปุ่มลบ 🗑️ แสดงผล 100%)
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=235)
        btn_frame.pack(side="right", padx=(3, 22))
        btn_frame.pack_propagate(False)
        
        # ดูรายละเอียด
        ctk.CTkButton(
            btn_frame,
            text="👁️",
            font=("Arial", 13),
            width=28,
            height=28,
            fg_color=COLORS["info"],
            command=lambda s=sale: self.view_sale_detail(s)
        ).pack(side="left", padx=1)
        
        # พิมพ์ใบเสร็จ
        ctk.CTkButton(
            btn_frame,
            text="🖨️",
            font=("Arial", 13),
            width=28,
            height=28,
            fg_color=COLORS["secondary"],
            command=lambda s=sale: self.print_receipt(s)
        ).pack(side="left", padx=1)
        
        # ส่งออก PDF (ใบเสร็จ)
        ctk.CTkButton(
            btn_frame,
            text="📄",
            font=("Arial", 13),
            width=28,
            height=28,
            fg_color="#6366f1",
            command=lambda s=sale: self.export_sale_to_pdf(s)
        ).pack(side="left", padx=1)
        
        # พิมพ์บิล A4 เต็มรูป
        ctk.CTkButton(
            btn_frame,
            text="A4",
            font=("Sarabun", 11, "bold"),
            width=34,
            height=28,
            fg_color="#10B981",
            command=lambda s=sale: self.open_a4_invoice_dialog(s)
        ).pack(side="left", padx=1)
        
        # ยกเลิกบิล (เฉพาะบิลที่ completed เท่านั้น)
        if not is_voided:
            ctk.CTkButton(
                btn_frame,
                text="🚫",
                font=("Arial", 13),
                width=28,
                height=28,
                fg_color=COLORS["warning"],
                hover_color=COLORS["danger"],
                command=lambda s=sale: self.void_sale(s)
            ).pack(side="left", padx=1)
        
        # ลบบิล (แสดงผลชัดเจน 100% ไม่ถูกบังโดย Scrollbar)
        ctk.CTkButton(
            btn_frame,
            text="🗑️",
            font=("Arial", 13),
            width=28,
            height=28,
            fg_color=COLORS["danger"],
            command=lambda s_id=sale['sale_id']: self.delete_single_sale(s_id)
        ).pack(side="left", padx=1)

        # เลขที่
        ctk.CTkLabel(
            row,
            text=sale['sale_number'],
            font=FONTS["body"],
            width=115,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # เวลา/วันที่
        try:
            sale_datetime = datetime.strptime(sale['sale_date'], DB_DATETIME_FORMAT)
            time_str = sale_datetime.strftime("%H:%M %d/%m")
        except:
            time_str = sale['sale_date'][:11]
            
        ctk.CTkLabel(
            row,
            text=time_str,
            font=FONTS["body"],
            width=95,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # จำนวนรายการ
        ctk.CTkLabel(
            row,
            text=str(sale['item_count']),
            font=FONTS["body"],
            width=45,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # ยอดรวม
        ctk.CTkLabel(
            row,
            text=f"฿{sale['subtotal']:,.2f}",
            font=FONTS["body"],
            width=80,
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # ส่วนลด
        ctk.CTkLabel(
            row,
            text=f"฿{sale['discount_amount']:,.2f}",
            font=FONTS["body"],
            width=65,
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
            width=90,
            text_color=total_color
        ).pack(side="left", padx=3)
        
        # พนักงาน
        ctk.CTkLabel(
            row,
            text=sale['cashier_name'] or "-",
            font=FONTS["small"],
            width=85,
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
            width=220,
            anchor="w",
            text_color="#999" if is_voided else COLORS["text_dark"]
        ).pack(side="left", padx=3)
        
        # ปุ่มจัดการ
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=240)
        btn_frame.pack(side="left", padx=3)
        btn_frame.pack_propagate(False)
        
        # ดูรายละเอียด
        ctk.CTkButton(
            btn_frame,
            text="👁️",
            font=("Arial", 14),
            width=30,
            height=30,
            fg_color=COLORS["info"],
            command=lambda s=sale: self.view_sale_detail(s)
        ).pack(side="left", padx=1)
        
        # พิมพ์ใบเสร็จ
        ctk.CTkButton(
            btn_frame,
            text="🖨️",
            font=("Arial", 14),
            width=30,
            height=30,
            fg_color=COLORS["secondary"],
            command=lambda s=sale: self.print_receipt(s)
        ).pack(side="left", padx=1)
        
        # ส่งออก PDF (ใบเสร็จ)
        ctk.CTkButton(
            btn_frame,
            text="📄",
            font=("Arial", 14),
            width=30,
            height=30,
            fg_color="#6366f1",
            command=lambda s=sale: self.export_sale_to_pdf(s)
        ).pack(side="left", padx=1)
        
        # พิมพ์บิล A4 เต็มรูป
        ctk.CTkButton(
            btn_frame,
            text="📄 A4",
            font=("Sarabun", 11, "bold"),
            width=40,
            height=30,
            fg_color="#10B981",
            command=lambda s=sale: self.open_a4_invoice_dialog(s)
        ).pack(side="left", padx=1)
        
        # ยกเลิกบิล (เฉพาะบิลที่ completed เท่านั้น)
        if not is_voided:
            ctk.CTkButton(
                btn_frame,
                text="🚫",
                font=("Arial", 14),
                width=30,
                height=30,
                fg_color=COLORS["warning"],
                hover_color=COLORS["danger"],
                command=lambda s=sale: self.void_sale(s)
            ).pack(side="left", padx=1)
        
        # ลบบิล
        ctk.CTkButton(
            btn_frame,
            text="🗑️",
            font=("Arial", 14),
            width=30,
            height=30,
            fg_color=COLORS["danger"],
            command=lambda s_id=sale['sale_id']: self.delete_single_sale(s_id)
        ).pack(side="left", padx=1)
        
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
        sale = dict(sale) if hasattr(sale, 'keys') else sale
        
        try:
            parent_win = self.winfo_toplevel()
            dialog = ctk.CTkToplevel(parent_win)
        except Exception:
            dialog = ctk.CTkToplevel(self)

        dialog.title(f"รายละเอียด - {sale.get('sale_number', '')}")
        dialog.geometry(get_responsive_dialog_geometry(self, 720, 620))
        
        try:
            dialog.transient(dialog.master)
        except Exception:
            pass
            
        dialog.lift()
        dialog.focus_force()
        try:
            dialog.grab_set()
        except Exception:
            pass

        is_voided = sale.get('status') in ('voided', 'returned')
        
        # ข้อมูลหลัก
        info_frame = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        status_text = "🚫 ยกเลิกแล้ว" if is_voided else "✅ ปกติ"
        cashier_name = sale.get('cashier_name') or '-'
        member_name = sale.get('member_name') or '-'
        payment_method = sale.get('payment_method') or 'เงินสด'
        price_type_name = PRICE_TYPES.get(sale.get('price_type', 'retail'), 'ราคาปกติ')
        
        info_text = (
            f"เลขที่บิล: {sale.get('sale_number', '-')}\n"
            f"วันที่/เวลา: {sale.get('sale_date', '-')}\n"
            f"ประเภทราคา: {price_type_name}\n"
            f"พนักงานขาย: {cashier_name}\n"
            f"สมาชิก/ลูกค้า: {member_name}\n"
            f"วิธีชำระเงิน: {payment_method}\n"
            f"สถานะ: {status_text}"
        )
        
        ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=FONTS["body"],
            justify="left",
            anchor="w"
        ).pack(padx=20, pady=15, fill="x")
        
        # รายการสินค้า
        ctk.CTkLabel(
            dialog,
            text="📦 รายการสินค้าในบิล",
            font=FONTS["heading"],
            text_color=COLORS["primary"]
        ).pack(pady=(5, 5))
        
        items_frame = ctk.CTkScrollableFrame(dialog, fg_color="white", corner_radius=10, height=220)
        items_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.db.connect()
        items = self.db.fetch_all(
            "SELECT * FROM sale_items WHERE sale_id = ?",
            (sale['sale_id'],)
        )
        self.db.disconnect()
        
        if items:
            for item in items:
                item_dict = dict(item) if hasattr(item, 'keys') else item
                item_row = ctk.CTkFrame(items_frame, fg_color=COLORS["light"], corner_radius=5)
                item_row.pack(fill="x", padx=5, pady=3)
                
                p_name = item_dict.get('product_name', 'สินค้า')
                q = item_dict.get('quantity', 0)
                u_price = item_dict.get('unit_price', 0.0)
                tot_price = item_dict.get('total_price', 0.0)
                
                ctk.CTkLabel(item_row, text=p_name, font=FONTS["body"], anchor="w", width=300).pack(side="left", padx=10, pady=8)
                ctk.CTkLabel(item_row, text=f"{q} x ฿{u_price:,.2f}", font=FONTS["body"], width=150).pack(side="left", padx=10)
                ctk.CTkLabel(item_row, text=f"฿{tot_price:,.2f}", font=("Sarabun", 14, "bold"), text_color=COLORS["success"]).pack(side="right", padx=10)
        else:
            ctk.CTkLabel(items_frame, text="ไม่พบรายการสินค้าในระบบ", font=FONTS["body"], text_color="gray").pack(pady=20)
        
        # สรุปยอด
        summary_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        summary_frame.pack(fill="x", padx=20, pady=(5, 15))
        
        subtotal = sale.get('subtotal', 0.0) or 0.0
        discount = sale.get('discount_amount', 0.0) or 0.0
        tax = sale.get('tax_amount', 0.0) or 0.0
        total = sale.get('total_amount', 0.0) or 0.0
        paid = sale.get('paid_amount', 0.0) or 0.0
        change = sale.get('change_amount', 0.0) or 0.0
        
        for label, value in [
            ("ยอดรวม:", f"฿{subtotal:,.2f}"),
            ("ส่วนลด:", f"฿{discount:,.2f}"),
            ("ภาษี VAT:", f"฿{tax:,.2f}"),
            ("ยอดสุทธิ:", f"฿{total:,.2f}"),
            ("รับเงิน:", f"฿{paid:,.2f}"),
            ("เงินทอน:", f"฿{change:,.2f}"),
        ]:
            row = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(row, text=label, font=FONTS["body"]).pack(side="left")
            ctk.CTkLabel(row, text=value, font=FONTS["body"],
                        text_color=COLORS["success"] if "ยอดสุทธิ" in label else COLORS["text_dark"]).pack(side="right")
        
        ctk.CTkButton(dialog, text="❌ ปิดหน้าต่าง", font=FONTS["button"], width=150, height=38, command=dialog.destroy).pack(pady=(0, 15))
    
    # ==========================================================
    # พิมพ์ใบเสร็จ
    # ==========================================================
    def print_receipt(self, sale):
        """พิมพ์ใบเสร็จ"""
        sale = dict(sale) if hasattr(sale, 'keys') else sale
        self.db.connect()
        items = self.db.fetch_all("SELECT * FROM sale_items WHERE sale_id = ?", (sale['sale_id'],))
        self.db.disconnect()
        
        receipt_data = {
            'company': COMPANY_INFO,
            'sale_number': sale.get('sale_number', ''),
            'sale_date': sale.get('sale_date', ''),
            'customer_name': sale.get('member_name') or sale.get('customer_name') or 'ลูกค้าทั่วไป',
            'cashier': sale.get('cashier_name', '-'),
            'items': [dict(item) for item in items],
            'subtotal': sale.get('subtotal', 0.0),
            'discount_amount': sale.get('discount_amount', 0.0),
            'tax_amount': sale.get('tax_amount', 0.0),
            'total_amount': sale.get('total_amount', 0.0),
            'paid_amount': sale.get('paid_amount', 0.0),
            'change_amount': sale.get('change_amount', 0.0)
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

    def export_sale_to_pdf(self, sale):
        """ส่งออกใบเสร็จเป็น PDF"""
        sale = dict(sale) if hasattr(sale, 'keys') else sale
        self.db.connect()
        items = self.db.fetch_all("SELECT * FROM sale_items WHERE sale_id = ?", (sale['sale_id'],))
        self.db.disconnect()
        
        customer_name = sale.get('member_name') or 'ลูกค้าทั่วไป'
        if sale.get('member_id') and not sale.get('member_name'):
            try:
                self.db.connect()
                m = self.db.fetch_one("SELECT name FROM members WHERE member_id = ?", (sale['member_id'],))
                self.db.disconnect()
                if m:
                    customer_name = m['name']
            except:
                pass
        
        receipt_data = {
            'company': COMPANY_INFO,
            'sale_number': sale.get('sale_number', ''),
            'sale_date': sale.get('sale_date', ''),
            'customer_name': customer_name,
            'cashier': sale.get('cashier_name', '-'),
            'items': [dict(item) for item in items],
            'subtotal': sale.get('subtotal', 0.0),
            'discount_amount': sale.get('discount_amount', 0.0),
            'tax_amount': sale.get('tax_amount', 0.0),
            'total_amount': sale.get('total_amount', 0.0),
            'paid_amount': sale.get('paid_amount', 0.0),
            'change_amount': sale.get('change_amount', 0.0)
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Receipt_{sale['sale_number']}.pdf"
        )
        
        if not filename:
            return
            
        try:
            from utils.pdf_utils import create_receipt_pdf
            if create_receipt_pdf(receipt_data, filename=filename, paper_size="A4"):
                messagebox.showinfo("สำเร็จ", f"ส่งออกไฟล์ PDF สำเร็จ!\nบันทึกที่: {filename}")
            else:
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถสร้างไฟล์ PDF ได้")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการสร้าง PDF:\n{e}")

    def open_a4_invoice_dialog(self, sale):
        """เปิด Dialog เพื่อแก้ไขหัวกระดาษและพิมพ์ใบเสร็จ/ใบกำกับภาษี A4 เต็มรูปแบบ"""
        sale = dict(sale) if hasattr(sale, 'keys') else sale
        sale_id = sale['sale_id']
        
        # ค้นหารายละเอียดล่าสุดจากฐานข้อมูลโดยตรง
        self.db.connect()
        sale_details = self.db.fetch_one("SELECT * FROM sales WHERE sale_id = ?", (sale_id,))
        self.db.disconnect()
        
        if not sale_details:
            messagebox.showerror("ข้อผิดพลาด", "ไม่พบข้อมูลบิลการขาย")
            return
            
        sale_details = dict(sale_details)
        
        # ดึงค่าเดิม
        current_name = sale_details.get('customer_name') or ''
        current_tax_id = sale_details.get('customer_tax_id') or ''
        current_address = sale_details.get('customer_address') or ''
        current_notes = sale_details.get('notes') or ''
        
        # ถ้าไม่มีชื่อลูกค้าในบิล แต่อาจดึงจากสมาชิก (ถ้ามี)
        if not current_name and sale_details.get('member_id'):
            try:
                self.db.connect()
                member = self.db.fetch_one("SELECT name, tax_id, address FROM members WHERE member_id = ?", (sale_details['member_id'],))
                self.db.disconnect()
                if member:
                    current_name = member['name'] or ''
                    current_tax_id = member['tax_id'] or ''
                    current_address = member['address'] or ''
            except:
                pass
        
        # สร้าง Toplevel window
        try:
            parent_win = self.winfo_toplevel()
            dialog = ctk.CTkToplevel(parent_win)
        except Exception:
            dialog = ctk.CTkToplevel(self)
            
        dialog.title(f"ใบเสร็จ A4 / ใบกำกับภาษีเต็มรูป - บิล {sale_details.get('sale_number')}")
        dialog.geometry(get_responsive_dialog_geometry(self, 560, 560))
        
        try:
            dialog.transient(dialog.master)
        except Exception:
            pass
            
        dialog.lift()
        dialog.focus_force()
        try:
            dialog.grab_set()
        except Exception:
            pass
            
        # UI Elements
        container = ctk.CTkFrame(dialog, fg_color="white", corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            container,
            text=f"📝 แก้ไขหัวเอกสาร & หมายเหตุ (บิล: {sale_details.get('sale_number')})",
            font=("Sarabun", 16, "bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # ช่องชื่อลูกค้า/บริษัท
        ctk.CTkLabel(container, text="ชื่อลูกค้า / บริษัท / ห้างร้าน:", font=FONTS["body"]).pack(anchor="w", padx=20, pady=(5, 2))
        name_entry = ctk.CTkEntry(container, font=FONTS["body"], height=35)
        name_entry.pack(fill="x", padx=20, pady=(0, 8))
        name_entry.insert(0, current_name)
        
        # ช่องเลขผู้เสียภาษี
        ctk.CTkLabel(container, text="เลขประจำตัวผู้เสียภาษี (13 หลัก):", font=FONTS["body"]).pack(anchor="w", padx=20, pady=(5, 2))
        tax_entry = ctk.CTkEntry(container, font=FONTS["body"], height=35)
        tax_entry.pack(fill="x", padx=20, pady=(0, 8))
        tax_entry.insert(0, current_tax_id)
        
        # ที่อยู่ลูกค้า
        ctk.CTkLabel(container, text="ที่อยู่จัดส่ง / ที่อยู่บริษัท:", font=FONTS["body"]).pack(anchor="w", padx=20, pady=(5, 2))
        address_textbox = ctk.CTkTextbox(container, font=FONTS["body"], height=60, border_width=1, border_color="#CBD5E1")
        address_textbox.pack(fill="x", padx=20, pady=(0, 8))
        address_textbox.insert("1.0", current_address)

        # หมายเหตุเพิ่มเติม
        ctk.CTkLabel(container, text="หมายเหตุเพิ่มเติม (ถ้าไม่ระบุจะใช้ข้อความเดิม):", font=FONTS["body"]).pack(anchor="w", padx=20, pady=(5, 2))
        note_entry = ctk.CTkEntry(container, font=FONTS["body"], height=35, placeholder_text="ระบุหมายเหตุเพิ่มเติม...")
        note_entry.pack(fill="x", padx=20, pady=(0, 15))
        note_entry.insert(0, current_notes)
        
        # ฟังก์ชันเมื่อกดบันทึก
        def do_save_and_print():
            new_name = name_entry.get().strip()
            new_tax_id = tax_entry.get().strip()
            new_address = address_textbox.get("1.0", "end-1c").strip()
            new_notes = note_entry.get().strip()
            
            # บันทึกลงฐานข้อมูล
            self.db.connect()
            success = self.db.execute(
                "UPDATE sales SET customer_name = ?, customer_tax_id = ?, customer_address = ?, notes = ? WHERE sale_id = ?",
                (new_name, new_tax_id, new_address, new_notes, sale_id)
            )
            self.db.disconnect()
            
            if not success:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกข้อมูลลงฐานข้อมูลได้")
                return
                
            # สร้างข้อมูล PDF
            # ดึงรายการสินค้า
            self.db.connect()
            items = self.db.fetch_all("""
                SELECT si.*, p.barcode, p.unit 
                FROM sale_items si 
                LEFT JOIN products p ON si.product_id = p.product_id 
                WHERE si.sale_id = ?
            """, (sale_id,))
            self.db.disconnect()
            
            # สรุปข้อมูลบริษัท
            receipt_data = {
                'company': COMPANY_INFO,
                'sale_number': sale_details.get('sale_number'),
                'sale_date': sale_details.get('sale_date'),
                'customer_name': new_name or 'ลูกค้าทั่วไป',
                'customer_tax_id': new_tax_id,
                'customer_address': new_address,
                'note': new_notes,
                'notes': new_notes,
                'cashier': sale.get('cashier_name') or sale_details.get('cashier_name') or '-',
                'payment_method': sale_details.get('payment_method', 'เงินสด'),
                'items': [dict(item) for item in items],
                'subtotal': sale_details.get('subtotal', 0.0),
                'discount_amount': sale_details.get('discount_amount', 0.0),
                'tax_amount': sale_details.get('tax_amount', 0.0),
                'total_amount': sale_details.get('total_amount', 0.0),
                'paid_amount': sale_details.get('paid_amount', 0.0),
                'change_amount': sale_details.get('change_amount', 0.0)
            }
            
            # ปิด dialog ก่อน
            dialog.destroy()
            
            # สร้าง PDF
            try:
                from utils.pdf_utils import create_full_receipt_a4
                ok, pdf_file = create_full_receipt_a4(receipt_data)
                if ok:
                    messagebox.showinfo("สำเร็จ", f"บันทึกและสร้าง PDF ใบเสร็จ A4 สำเร็จ!\n\nเปิดไฟล์: {pdf_file}")
                    # เปิดไฟล์ PDF ทันที
                    import os
                    os.startfile(os.path.abspath(pdf_file))
                else:
                    messagebox.showerror("ผิดพลาด", f"ไม่สามารถสร้าง PDF ได้: {pdf_file}")
            except Exception as ex:
                messagebox.showerror("ผิดพลาด", f"เกิดข้อผิดพลาดในการสร้าง PDF:\n{ex}")
                
            # โหลดตารางใหม่
            self.load_sales_history()
            
        # ปุ่มดำเนินการ
        button_row = ctk.CTkFrame(container, fg_color="transparent")
        button_row.pack(fill="x", padx=20, pady=(5, 15))
        
        ctk.CTkButton(
            button_row,
            text="💾 บันทึกข้อมูล & พิมพ์ A4",
            font=("Sarabun", 13, "bold"),
            fg_color=COLORS["success"],
            hover_color="#059669",
            height=38,
            command=do_save_and_print
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            button_row,
            text="❌ ยกเลิก",
            font=("Sarabun", 13),
            fg_color="#64748B",
            hover_color="#475569",
            height=38,
            command=dialog.destroy
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def export_history_to_excel(self):
        """ส่งออกประวัติการขายตามที่ค้นหาเป็น Excel"""
        try:
            filter_start = self.start_date.get_date()
            filter_end = self.end_date.get_date()
            start = filter_start.strftime("%Y-%m-%d")
            end = filter_end.strftime("%Y-%m-%d")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"กรุณาเลือกวันที่ที่ถูกต้อง: {e}")
            return
            
        params = [f"{start} 00:00:00", f"{end} 23:59:59"]
        search_query = ""
        
        keyword = self.search_entry.get().strip()
        if keyword:
            search_query = """ AND (
                s.sale_number LIKE ? 
                OR m.name LIKE ? 
                OR m.phone LIKE ? 
                OR u.full_name LIKE ? 
                OR si.product_name LIKE ?
            )"""
            params.extend([f"%{keyword}%"] * 5)
            
        self.db.connect()
        sales = self.db.fetch_all(f"""
            SELECT s.sale_id, s.sale_number, s.sale_date,
                   s.subtotal, s.discount_amount, s.tax_amount, 
                   s.total_amount, s.paid_amount, s.change_amount, 
                   s.payment_method, s.status,
                   u.full_name as cashier_name,
                   m.name as member_name,
                   GROUP_CONCAT(si.product_name || ' x' || si.quantity) as items
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            LEFT JOIN members m ON s.member_id = m.member_id
            WHERE s.sale_date >= ? AND s.sale_date <= ? {search_query}
            GROUP BY s.sale_id
            ORDER BY s.sale_date DESC
        """, tuple(params))
        self.db.disconnect()
        
        if not sales:
            messagebox.showwarning("แจ้งเตือน", "ไม่มีข้อมูลประวัติขายตามเงื่อนไขที่เลือก")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"SalesHistory_{start}_to_{end}.xlsx"
        )
        
        if not filename:
            return
            
        columns = [
            "เลขที่บิล", "วันที่/เวลา", "สมาชิก", "ยอดรวม", "ส่วนลด", "ภาษี", 
            "ยอดสุทธิ", "รับเงิน", "เงินทอน", "วิธีชำระ", "สถานะ",
            "พนักงาน", "รายการสินค้า"
        ]
        
        export_data = []
        for sale in sales:
            export_data.append({
                "เลขที่บิล": sale['sale_number'],
                "วันที่/เวลา": sale['sale_date'],
                "สมาชิก": sale['member_name'] or 'ลูกค้าทั่วไป',
                "ยอดรวม": sale['subtotal'],
                "ส่วนลด": sale['discount_amount'],
                "ภาษี": sale['tax_amount'],
                "ยอดสุทธิ": sale['total_amount'],
                "รับเงิน": sale['paid_amount'],
                "เงินทอน": sale['change_amount'],
                "วิธีชำระ": sale['payment_method'],
                "สถานะ": sale['status'],
                "พนักงาน": sale['cashier_name'],
                "รายการสินค้า": sale['items'] or '-'
            })
        
        success = ExcelManager.export_to_excel(
            export_data,
            columns,
            filename,
            sheet_name="Sales History",
            title=f"รายงานประวัติการขาย ({start} ถึง {end})"
        )
        
        if success:
            messagebox.showinfo("สำเร็จ", f"Export ประวัติการขายสำเร็จ 100%!\nบันทึกที่: {filename}")
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถบันทึกไฟล์ Excel ได้")
