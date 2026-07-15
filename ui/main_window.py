# -*- coding: utf-8 -*-
"""
หน้าหลักของโปรแกรม (Main Window)
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
from datetime import datetime
import sys
from PIL import Image, ImageOps


class MainWindow:
    """หน้าหลักของโปรแกรม"""
    
    def __init__(self, user_id, user_info):
        self.window = ctk.CTk()
        self.window.title(APP_NAME)
        self.window.geometry(WINDOW_SIZE)
        self.window.minsize(*MIN_WINDOW_SIZE)
        
        # ตั้งค่าไอคอนหน้าต่าง
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Error loading icon: {e}")
        
        # ข้อมูลผู้ใช้
        self.user_id = user_id
        self.user_info = user_info
        
        # Database
        self.db = DatabaseManager()
        
        # ตัวแปร
        self.current_page = None
        
        # สร้าง UI
        self.create_layout()
        self.show_dashboard()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # F1 Global Shortcut: กดจากหน้าไหนก็ได้ → ไปหน้า POS + focus ช่องสแกน
        self.window.bind("<F1>", lambda e: self.goto_pos_and_scan())
        
    def create_layout(self):
        """สร้างโครงสร้างหน้าหลัก"""
        # แถบด้านบน (Header)
        self.create_header()
        
        # เนื้อหาหลัก
        content_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)
        
        # แถบด้านข้าง (Sidebar)
        self.create_sidebar(content_frame)
        
        # พื้นที่เนื้อหา
        self.content_area = ctk.CTkFrame(content_frame, fg_color=COLORS["light"])
        self.content_area.pack(side="right", fill="both", expand=True)
        
    def create_header(self):
        """สร้างแถบด้านบน"""
        header = ctk.CTkFrame(self.window, height=70, fg_color=COLORS["primary"])
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        # ชื่อโปรแกรม
        title_label = ctk.CTkLabel(
            header,
            text="🏪 " + APP_NAME,
            font=FONTS["heading"],
            text_color="white"
        )
        title_label.pack(side="left", padx=20)
        
        # ข้อมูลผู้ใช้และเวลา
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="right", padx=20)
        
        # เวลา
        self.time_label = ctk.CTkLabel(
            user_frame,
            text=datetime.now().strftime(DATETIME_FORMAT),
            font=FONTS["small"],
            text_color="white"
        )
        self.time_label.pack(anchor="e")
        
        # ชื่อผู้ใช้
        user_label = ctk.CTkLabel(
            user_frame,
            text=f"👤 {self.user_info['full_name']} ({USER_ROLES[self.user_info['role']]})",
            font=FONTS["body"],
            text_color="white"
        )
        user_label.pack(anchor="e", pady=(5, 0))
        
        # อัพเดทเวลาทุกวินาที
        self.update_time()
        
    def update_time(self):
        """อัพเดทเวลาปัจจุบัน (ทุก 10 วินาทีเพื่อประหยัด CPU)"""
        current_time = datetime.now().strftime(DATETIME_FORMAT)
        self.time_label.configure(text=current_time)
        self.window.after(10000, self.update_time)  # 10 วินาที (ลดจาก 1 วินาที)
        
    def create_sidebar(self, parent):
        """สร้างแถบเมนูด้านข้าง"""
        sidebar = ctk.CTkFrame(parent, width=250, fg_color=COLORS["dark"])
        sidebar.pack(side="left", fill="y", padx=0, pady=0)
        sidebar.pack_propagate(False)
        
        # เมนูหลัก (ไม่มีอิโมจิ — ชิดซ้าย ตัวหนา)
        menu_items = [
            ("หน้าหลัก", "dashboard", "all"),
            ("ขายสินค้า", "pos", ["manage_sales"]),
            ("จัดการสินค้า", "products", ["manage_products", "view_products"]),
            ("ประวัติการขาย", "history", ["view_history"]),
            ("คืนสินค้า", "returns", ["manage_sales"]),
            ("จัดการสต็อก", "stock", ["manage_stock"]),
            ("จัดการผู้ใช้", "users", ["manage_users"]),
            ("รายงานยอดขาย", "reports", ["view_reports"]),
            ("ตั้งค่า", "settings", "all"),
            ("วิธีใช้งาน", "help", "all"),
        ]
        
        # สร้างปุ่มเมนู
        self.menu_buttons = {}
        for text, page_id, permissions in menu_items:
            # ตรวจสอบสิทธิ์
            if not self.check_permission(permissions):
                continue
                
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                font=("Sarabun", 16, "bold"),
                height=50,
                fg_color="transparent",
                hover_color=COLORS["primary"],
                anchor="w",
                command=lambda p=page_id: self.change_page(p)
            )
            btn.pack(fill="x", padx=10, pady=5)
            self.menu_buttons[page_id] = btn
            
        # ปุ่มออกจากระบบ
        logout_btn = ctk.CTkButton(
            sidebar,
            text="ออกจากระบบ",
            font=("Sarabun", 16, "bold"),
            height=50,
            fg_color=COLORS["danger"],
            hover_color="#cc0000",
            command=self.logout
        )
        logout_btn.pack(side="bottom", fill="x", padx=10, pady=10)
        
    def check_permission(self, required_permissions):
        """ตรวจสอบสิทธิ์การเข้าถึง"""
        if required_permissions == "all":
            return True
            
        user_role = self.user_info['role']
        
        # Admin มีสิทธิ์ทั้งหมด
        if user_role == "admin":
            return True
            
        # ตรวจสอบสิทธิ์ตาม role
        user_permissions = PERMISSIONS.get(user_role, [])
        
        if "all" in user_permissions:
            return True
            
        # ตรวจสอบว่ามีสิทธิ์อย่างน้อย 1 อย่าง
        for perm in required_permissions:
            if perm in user_permissions:
                return True
                
        return False
        
    def change_page(self, page_id):
        """เปลี่ยนหน้า"""
        # Reset สีปุ่มทั้งหมด
        for btn in self.menu_buttons.values():
            btn.configure(fg_color="transparent")
            
        # เปลี่ยนสีปุ่มที่เลือก
        if page_id in self.menu_buttons:
            self.menu_buttons[page_id].configure(fg_color=COLORS["primary"])
            
        # ล้างเนื้อหาเดิม
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
        # แสดงหน้าที่เลือก
        self.current_page = page_id
        
        if page_id == "dashboard":
            self.show_dashboard()
        elif page_id == "pos":
            self.show_pos()
        elif page_id == "products":
            self.show_products()
        elif page_id == "reports":
            self.show_reports()
        elif page_id == "history":
            self.show_history()
        elif page_id == "returns":
            self.show_returns()
        elif page_id == "stock":
            self.show_stock()
        elif page_id == "users":
            self.show_users()
        elif page_id == "settings":
            self.show_settings()
        elif page_id == "brands":
            self.show_brands()
        elif page_id == "vendors":
            self.show_vendors()
        elif page_id == "help":
            self.show_help()
            
    def show_dashboard(self):
        """แสดงหน้า Dashboard"""
        # หัวข้อ
        title = ctk.CTkLabel(
            self.content_area,
            text="📊 แดชบอร์ด",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(pady=20, padx=20, anchor="w")
        
        # สถิติสรุป
        stats_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        # ดึงข้อมูลสถิติ (รวมเป็น query เดียว เพื่อลดเวลาเชื่อมต่อ DB)
        self.db.connect()
        
        today = datetime.now().strftime(DB_DATE_FORMAT)
        current_month = datetime.now().strftime("%Y-%m")
        
        # Query รวม — ลด DB round-trips จาก 4 เหลือ 1 (Performance)
        stats_result = self.db.fetch_one("""
            SELECT 
                (SELECT COUNT(*) FROM sales WHERE sale_date LIKE ? AND status = 'completed') as sales_count,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE sale_date LIKE ? AND status = 'completed') as sales_total,
                (SELECT COUNT(*) FROM products WHERE is_active = 1) as products_count,
                (SELECT COUNT(*) FROM products WHERE stock_quantity <= min_stock AND is_active = 1) as low_stock,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE sale_date LIKE ? AND status = 'completed') as month_total
        """, (f"{today}%", f"{today}%", f"{current_month}%"))
        
        self.db.disconnect()
        
        # การ์ดสถิติ
        stats = [
            ("💰 ยอดขายวันนี้", f"{stats_result['sales_total']:,.2f} ฿", f"{stats_result['sales_count']} รายการ", COLORS["success"]),
            ("📅 ยอดเดือนนี้", f"{stats_result['month_total'] or 0:,.2f} ฿", "ยอดขายรวมเดือนนี้", COLORS["primary"]),
            ("📦 จำนวนสินค้า", f"{stats_result['products_count']} รายการ", "สินค้าในระบบ", COLORS["info"]),
            ("⚠️ สินค้าใกล้หมด", f"{stats_result['low_stock']} รายการ", "ต้องเติมสต็อก", COLORS["warning"]),
        ]
        
        for title_text, value, subtitle, color in stats:
            card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=15)
            card.pack(side="left", fill="both", expand=True, padx=10)
            
            card_title = ctk.CTkLabel(
                card,
                text=title_text,
                font=FONTS["body"],
                text_color="white"
            )
            card_title.pack(pady=(20, 10))
            
            card_value = ctk.CTkLabel(
                card,
                text=value,
                font=("Sarabun", 32, "bold"),
                text_color="white"
            )
            card_value.pack()
            
            card_subtitle = ctk.CTkLabel(
                card,
                text=subtitle,
                font=FONTS["small"],
                text_color="white"
            )
            card_subtitle.pack(pady=(5, 20))
            
        
        
    def goto_pos_and_scan(self):
        """F1: ไปหน้า POS แล้ว focus ที่ช่องสแกนบาร์โค้ดทันที"""
        if self.current_page == "pos" and hasattr(self, '_pos_frame') and self._pos_frame:
            # ถ้าอยู่หน้า POS อยู่แล้ว → focus ช่องสแกนเลย
            try:
                self._pos_frame.search_entry.delete(0, 'end')
                self._pos_frame.search_entry.focus()
            except Exception:
                pass
        else:
            # ถ้าอยู่หน้าอื่น → เปลี่ยนไปหน้า POS
            self.change_page("pos")

    def show_pos(self):
        """แสดงหน้าขายสินค้า"""
        from ui.pos_window import POSFrame
        
        pos_frame = POSFrame(self.content_area, self.user_id, self.user_info)
        pos_frame.pack(fill="both", expand=True)
        self._pos_frame = pos_frame
        
        # Auto focus ช่องสแกนบาร์โค้ดทันที
        self.window.after(100, lambda: pos_frame.search_entry.focus())
        
    def show_products(self):
        """แสดงหน้าจัดการสินค้า"""
        from ui.product_window import ProductManagementFrame
        
        product_frame = ProductManagementFrame(self.content_area, self.user_id)
        product_frame.pack(fill="both", expand=True)
        
    def show_reports(self):
        """แสดงหน้ารายงาน"""
        from .reports_window import ReportsFrame
        frame = ReportsFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)
        
    def show_history(self):
        """แสดงหน้าประวัติการขาย"""
        from .history_window import SalesHistoryFrame
        frame = SalesHistoryFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)
        
    def show_returns(self):
        """แสดงหน้าคืนสินค้า"""
        from .returns_window import ReturnsFrame
        frame = ReturnsFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)
        
    def show_stock(self):
        """แสดงหน้าจัดการสต็อก"""
        from .stock_window import StockManagementFrame
        frame = StockManagementFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)
        
    def show_users(self):
        """แสดงหน้าจัดการผู้ใช้"""
        from .users_window import UsersManagementFrame
        frame = UsersManagementFrame(self.content_area, self.user_id, self.user_info['role'])
        frame.pack(fill="both", expand=True)
        
        info = ctk.CTkLabel(
            self.content_area,
            text="หน้าจัดการผู้ใช้ - กำลังพัฒนา",
            font=FONTS["body"]
        )
        info.pack(pady=50)
        
    def show_settings(self):
        """แสดงหน้าตั้งค่า"""
        from .settings_window import SettingsFrame
        frame = SettingsFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)

    def show_brands(self):
        """แสดงหน้าจัดการแบรนด์"""
        from .brand_window import BrandManagementFrame
        frame = BrandManagementFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)

    def show_vendors(self):
        """แสดงหน้าจัดการผู้จัดจำหน่าย"""
        from .vendor_window import VendorManagementFrame
        frame = VendorManagementFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)

    def show_help(self):
        """แสดงหน้าวิธีใช้งาน"""
        from .help_window import HelpGuideFrame
        frame = HelpGuideFrame(self.content_area, self.user_id)
        frame.pack(fill="both", expand=True)
        
    def logout(self):
        """ออกจากระบบ"""
        result = messagebox.askyesno(
            "ออกจากระบบ",
            "คุณต้องการออกจากระบบใช่หรือไม่?"
        )
        
        if result:
            self.window.destroy()
            sys.exit(0)
            
    def on_closing(self):
        """จัดการเมื่อปิดหน้าต่าง"""
        self.logout()
        
    def run(self):
        """เริ่มโปรแกรม"""
        self.window.mainloop()


if __name__ == "__main__":
    # ทดสอบ
    class TestUser:
        pass
    
    user_info = TestUser()
    user_info.__dict__ = {
        'user_id': 1,
        'username': 'admin',
        'full_name': 'ผู้ดูแลระบบ',
        'role': 'admin',
        'email': None,
        'phone': None,
        'is_active': 1
    }
    
    app = MainWindow(1, user_info)
    app.run()
