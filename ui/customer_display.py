# -*- coding: utf-8 -*-
"""
Customer Display - จอแสดงผลสำหรับลูกค้า (Pastel Minimal Design)
แสดงรายการสินค้า + ยอดรวม + QR Code PromptPay
"""

import customtkinter as ctk
from tkinter import messagebox
from config import *
import qrcode
from PIL import Image, ImageTk
import io
import os
from database import DatabaseManager


# 🎨 Pastel Color Palette (Minimal & Modern)
PASTEL_COLORS = {
    "bg_main": "#F5F5F5",           # เทาอ่อนพาสเทล (พื้นหลังหลัก)
    "bg_card": "#FFFFFF",           # ขาวสะอาด (การ์ด)
    "bg_header": "#E8F5E9",         # เขียวพาสเทลอ่อนมาก
    "primary": "#81C784",           # เขียวพาสเทล
    "primary_dark": "#66BB6A",      # เขียวพาสเทลเข้ม
    "accent": "#FFB74D",            # ส้มพาสเทล
    "text_dark": "#37474F",         # เทาเข้ม
    "text_light": "#78909C",        # เทาอ่อน
    "divider": "#ECEFF1",           # เส้นแบ่ง
    "success": "#4CAF50",           # เขียวสด (ยอดเงิน)
    "highlight": "#FFF9C4",         # เหลืองพาสเทลอ่อน
}


class CustomerDisplayWindow(ctk.CTkToplevel):
    """หน้าต่างแสดงผลสำหรับลูกค้า (จอที่ 2) - Pastel Minimal Style"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("🛒 จอแสดงผลลูกค้า - Customer Display")
        
        # ตั้งค่า fullscreen แบบสมบูรณ์ (ซ่อน Taskbar)
        self.is_fullscreen = True
        self.attributes('-fullscreen', True)
        self.overrideredirect(True) # ซ่อนแถบหัวหน้าต่างและ Taskbar
        
        self.configure(fg_color=PASTEL_COLORS["bg_main"])
        
        # ข้อมูล
        self.cart_items = []
        self.total_amount = 0
        self.qr_code_data = ""
        self.db = DatabaseManager()
        
        self.create_widgets()
        
        # Bind เพื่อควบคุมหน้าต่าง
        self.bind("<Escape>", lambda e: self.toggle_fullscreen(False))
        self.bind("<F11>", lambda e: self.toggle_fullscreen(True))

    def toggle_fullscreen(self, mode):
        """สลับโหมดหน้าจอ"""
        self.is_fullscreen = mode
        self.overrideredirect(mode)
        self.attributes('-fullscreen', mode)
        if not mode:
            self.geometry("1024x768") # ขนาดเมื่อไม่ได้เต็มจอ
    
    def create_widgets(self):
        """สร้าง UI - Pastel Minimal Design"""
        # Header - ชื่อร้าน (Soft & Clean)
        header_frame = ctk.CTkFrame(
            self, 
            fg_color=PASTEL_COLORS["bg_header"], 
            height=100,
            corner_radius=0
        )
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True)
        
        # ไอคอนร้าน
        ctk.CTkLabel(
            header_content,
            text="🛒",
            font=("Arial", 40)
        ).pack(side="left", padx=(0, 15))
        
        # ชื่อร้าน
        ctk.CTkLabel(
            header_content,
            text=COMPANY_INFO['name'],
            font=("Sarabun", 42, "bold"),
            text_color=PASTEL_COLORS["primary_dark"]
        ).pack(side="left")
        
        # Main content with padding
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=30)
        
        # แบ่งเป็น 2 ส่วน: รายการสินค้า (ซ้าย 65%) และสรุป+QR (ขวา 35%)
        # ส่วนซ้าย - รายการสินค้า
        left_frame = ctk.CTkFrame(
            content, 
            fg_color=PASTEL_COLORS["bg_card"], 
            corner_radius=20,
            border_width=0
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))
        
        # Header ตาราง (Minimal)
        table_header = ctk.CTkFrame(
            left_frame, 
            fg_color=PASTEL_COLORS["primary"],
            corner_radius=15,
            height=55
        )
        table_header.pack(fill="x", padx=15, pady=15)
        table_header.pack_propagate(False)
        
        headers = [
            ("📦 รายการสินค้า", 400),
            ("จำนวน", 100),
            ("ราคา/หน่วย", 150),
            ("รวม", 150)
        ]
        
        for text, width in headers:
            ctk.CTkLabel(
                table_header,
                text=text,
                font=("Sarabun", 22, "bold"),
                text_color="white",
                width=width
            ).pack(side="left", padx=15)
        
        # รายการสินค้า (Scrollable with soft style)
        self.items_container = ctk.CTkScrollableFrame(
            left_frame,
            fg_color="transparent",
            scrollbar_button_color=PASTEL_COLORS["primary"],
            scrollbar_button_hover_color=PASTEL_COLORS["primary_dark"]
        )
        self.items_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # ส่วนขวา - สรุปและ QR
        right_frame = ctk.CTkFrame(
            content, 
            fg_color=PASTEL_COLORS["bg_card"], 
            corner_radius=20, 
            width=420
        )
        right_frame.pack(side="right", fill="y", padx=(15, 0))
        right_frame.pack_propagate(False)
        
        # สรุปยอด (Beautiful Card)
        summary_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        summary_frame.pack(fill="x", padx=25, pady=25)
        
        # จำนวนรายการ (อยู่ด้านบน)
        items_count_frame = ctk.CTkFrame(
            summary_frame,
            fg_color=PASTEL_COLORS["highlight"],
            corner_radius=12,
            height=50
        )
        items_count_frame.pack(fill="x", pady=(0, 15))
        items_count_frame.pack_propagate(False)
        
        self.items_count_label = ctk.CTkLabel(
            items_count_frame,
            text="0 รายการ",
            font=("Sarabun", 20, "bold"),
            text_color=PASTEL_COLORS["text_dark"]
        )
        self.items_count_label.pack(expand=True)
        
        # ยอดรวมทั้งสิ้น (Prominent Card)
        total_label_frame = ctk.CTkFrame(
            summary_frame, 
            fg_color=PASTEL_COLORS["primary"],
            corner_radius=15
        )
        total_label_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            total_label_frame,
            text="💰 ยอดรวมทั้งสิ้น",
            font=("Sarabun", 24, "bold"),
            text_color="white"
        ).pack(pady=(20, 5))
        
        self.total_label = ctk.CTkLabel(
            total_label_frame,
            text="฿0.00",
            font=("Sarabun", 52, "bold"),
            text_color="white"
        )
        self.total_label.pack(pady=(0, 20))
        
        # QR Code Frame (Clean Design)
        qr_frame = ctk.CTkFrame(
            right_frame, 
            fg_color="white",
            corner_radius=15,
            border_width=2,
            border_color=PASTEL_COLORS["divider"]
        )
        qr_frame.pack(fill="both", expand=True, padx=25, pady=(0, 25))
        
        ctk.CTkLabel(
            qr_frame,
            text="📱 สแกนเพื่อชำระเงิน",
            font=("Sarabun", 20, "bold"),
            text_color=PASTEL_COLORS["primary_dark"]
        ).pack(pady=(20, 10))
        
        self.qr_label = ctk.CTkLabel(
            qr_frame,
            text="",
            fg_color="white"
        )
        self.qr_label.pack(pady=(10, 20))

        # Payment Info (Received/Change) - Hidden by default or shown when paying
        self.payment_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.payment_frame.pack(fill="x", padx=25, pady=(0, 20))
        
        # Received
        received_frame = ctk.CTkFrame(self.payment_frame, fg_color="transparent")
        received_frame.pack(fill="x")
        ctk.CTkLabel(received_frame, text="รับเงิน:", font=("Sarabun", 18), text_color=PASTEL_COLORS["text_light"]).pack(side="left")
        self.received_amount_label = ctk.CTkLabel(received_frame, text="฿0.00", font=("Sarabun", 20, "bold"), text_color=PASTEL_COLORS["text_dark"])
        self.received_amount_label.pack(side="right")
        
        # Change
        change_frame = ctk.CTkFrame(self.payment_frame, fg_color=PASTEL_COLORS["highlight"], corner_radius=10)
        change_frame.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(change_frame, text="เงินทอน:", font=("Sarabun", 20, "bold"), text_color=PASTEL_COLORS["text_dark"]).pack(side="left", padx=15, pady=10)
        self.change_amount_label = ctk.CTkLabel(change_frame, text="฿0.00", font=("Sarabun", 28, "bold"), text_color=PASTEL_COLORS["success"])
        self.change_amount_label.pack(side="right", padx=15, pady=10)
        
        # Hide initially
        self.payment_frame.pack_forget()

        # Footer (Minimal & Friendly)
        footer = ctk.CTkFrame(
            self, 
            fg_color=PASTEL_COLORS["bg_header"],
            height=60,
            corner_radius=0
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        ctk.CTkLabel(
            footer,
            text="ขอบคุณที่ใช้บริการ 🙏 • Thank you!",
            font=("Sarabun", 22),
            text_color=PASTEL_COLORS["text_light"]
        ).pack(pady=15)
    
    def update_display(self, cart_items, total_amount, qr_data=None, paid=0, change=0):
        """อัพเดทการแสดงผล - Pastel Minimal Style"""
        self.cart_items = cart_items
        self.total_amount = total_amount
        
        # ล้างรายการเดิม
        for widget in self.items_container.winfo_children():
            widget.destroy()
        
        # แสดงรายการใหม่ (Soft & Clean Design)
        for idx, item in enumerate(cart_items):
            # สลับสีแบบ Subtle
            if idx % 2 == 0:
                bg = "#FAFAFA"  # ขาวอมเทาอ่อนมาก
            else:
                bg = "white"
            
            item_frame = ctk.CTkFrame(
                self.items_container,
                fg_color=bg,
                corner_radius=10,
                height=80  # เพิ่มความสูงเพื่อรองรับรูปภาพ
            )
            item_frame.pack(fill="x", pady=5, padx=5)
            item_frame.pack_propagate(False)
            
            # --- ส่วนรูปภาพสินค้า ---
            image_container = ctk.CTkFrame(item_frame, fg_color="transparent", width=70)
            image_container.pack(side="left", padx=(10, 5))
            image_container.pack_propagate(False)

            img_path = item.get('image_path')
            img_display = None
            if img_path and os.path.exists(img_path):
                img_display = self.load_item_image(img_path)
            
            if img_display:
                img_label = ctk.CTkLabel(image_container, image=img_display, text="")
                img_label.image = img_display
                img_label.pack(expand=True)
            else:
                ctk.CTkLabel(image_container, text="📦", font=("Arial", 24)).pack(expand=True)
            
            # ชื่อสินค้า
            name_text = item['name'] if 'name' in item else item.get('product_name', 'สินค้า')
            ctk.CTkLabel(
                item_frame,
                text=name_text[:40],
                font=("Sarabun", 20),
                text_color=PASTEL_COLORS["text_dark"],
                width=330,  # ปรับลดความกว้างเพื่อหลีกให้รูป
                anchor="w"
            ).pack(side="left", padx=10)
            
            # จำนวน (Highlighted)
            qty_frame = ctk.CTkFrame(
                item_frame,
                fg_color=PASTEL_COLORS["highlight"],
                corner_radius=8,
                width=70,
                height=40
            )
            qty_frame.pack(side="left", padx=10)
            qty_frame.pack_propagate(False)
            
            ctk.CTkLabel(
                qty_frame,
                text=str(item['quantity']),
                font=("Sarabun", 20, "bold"),
                text_color=PASTEL_COLORS["text_dark"]
            ).pack(expand=True)
            
            # ราคา/หน่วย
            price = item.get('price', item.get('unit_price', 0))
            ctk.CTkLabel(
                item_frame,
                text=f"฿{price:,.2f}",
                font=("Sarabun", 20),
                text_color=PASTEL_COLORS["text_light"],
                width=150
            ).pack(side="left", padx=10)
            
            # รวม (Bold & Accent)
            ctk.CTkLabel(
                item_frame,
                text=f"฿{item['total']:,.2f}",
                font=("Sarabun", 22, "bold"),
                text_color=PASTEL_COLORS["accent"],
                width=150
            ).pack(side="left", padx=10)
        
        # อัพเดทยอดรวม
        self.total_label.configure(text=f"฿{total_amount:,.2f}")
        
        # อัพเดทจำนวนรายการ
        count_text = f"🛒 {len(cart_items)} รายการ" if len(cart_items) > 0 else "ไม่มีสินค้า"
        self.items_count_label.configure(text=count_text)
        
        # อัพเดทข้อมูลการชำระเงิน
        if paid > 0:
            self.payment_frame.pack(fill="x", padx=25, pady=(0, 20))
            self.received_amount_label.configure(text=f"฿{paid:,.2f}")
            self.change_amount_label.configure(text=f"฿{max(0, change):,.2f}")
        else:
            self.payment_frame.pack_forget()

        # อัพเดท QR Code
        if qr_data:
            self.generate_qr_code(qr_data)
        else:
            # แสดง placeholder สวยๆ
            self.show_qr_placeholder()
    
    def generate_qr_code(self, data):
        """สร้าง QR Code สำหรับชำระเงิน - รองรับทั้งรูปภาพกำหนดเองและ Auto-generate"""
        try:
            # 1. ตรวจสอบก่อนว่ามีการตั้งค่ารูป QR กำหนดเองหรือไม่
            self.db.connect()
            qr_setting = self.db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
            self.db.disconnect()
            
            custom_qr_path = qr_setting['setting_value'] if qr_setting and qr_setting['setting_value'] else None
            
            if custom_qr_path and os.path.exists(custom_qr_path):
                # โหลดรูปภาพที่ผู้ใช้เลือกเอง
                img = Image.open(custom_qr_path)
                # ปรับขนาดให้พอดีกับกรอบ 280x280 (ใช้ Resampling.LANCZOS เพื่อความชัด)
                img.thumbnail((280, 280), Image.Resampling.LANCZOS)
                
                # สร้างภาพพื้นหลังขาวขนาด 280x280 เพื่อให้รูปอยู่กลาง
                bg = Image.new('RGB', (280, 280), 'white')
                img_w, img_h = img.size
                bg.paste(img, ((280 - img_w) // 2, (280 - img_h) // 2))
                
                photo = ImageTk.PhotoImage(bg)
                self.qr_label.configure(image=photo)
                self.qr_label.image = photo
                return

            # 2. ถ้าไม่มีรูปกำหนดเอง ให้สร้าง PromptPay QR ตามปกติ
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(
                fill_color=PASTEL_COLORS["primary_dark"],
                back_color="white"
            )
            img = img.resize((280, 280), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.qr_label.configure(image=photo)
            self.qr_label.image = photo
        except Exception as e:
            print(f"Error generating QR code: {e}")
            self.show_qr_placeholder()
    
    def show_qr_placeholder(self):
        """แสดง placeholder เมื่อยังไม่มี QR Code"""
        try:
            # สร้างรูป placeholder สวยๆ
            from PIL import Image, ImageDraw
            
            # สร้างภาพ
            img = Image.new('RGB', (280, 280), 'white')
            draw = ImageDraw.Draw(img)
            
            # วาดกรอบ
            draw.rectangle(
                [(20, 20), (260, 260)],
                outline=PASTEL_COLORS["divider"],
                width=3
            )
            
            # วาดไอคอน (วงกลม + ข้อความ)
            draw.ellipse(
                [(90, 90), (190, 190)],
                fill=PASTEL_COLORS["bg_header"]
            )
            
            # แปลงเป็น PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # แสดงผล
            self.qr_label.configure(image=photo)
            self.qr_label.image = photo
        except:
            # ถ้าสร้างไม่ได้ ให้แสดงข้อความ
            self.qr_label.configure(image="", text="📱\nรอสแกน QR Code")
    
    def clear_display(self):
        """ล้างหน้าจอ"""
        self.update_display([], 0, None)

    def load_item_image(self, path):
        """โหลดและปรับขนาดรูปสินค้าสำหรับแถวรายการ"""
        try:
            img = Image.open(path)
            # ปรับขนาดให้พอดีกับแถว (สูง 70px)
            img.thumbnail((70, 70), Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=img, dark_image=img, size=(60, 60))
        except:
            return None


def open_customer_display(parent):
    """เปิดหน้าต่างแสดงผลลูกค้า"""
    try:
        display = CustomerDisplayWindow(parent)
        return display
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดจอลูกค้าได้:\n{e}")
        return None


if __name__ == "__main__":
    # ทดสอบ
    root = ctk.CTk()
    root.withdraw()
    
    display = open_customer_display(root)
    
    # ทดสอบข้อมูล
    test_items = [
        {'product_name': 'น้ำดื่ม 600ml', 'quantity': 2, 'unit_price': 10, 'total': 20},
        {'product_name': 'ขนมปัง', 'quantity': 1, 'unit_price': 35, 'total': 35},
    ]
    
    if display:
        display.update_display(test_items, 55, "00020199530303986150120000123456789021508021506310102THง")
    
    root.mainloop()
