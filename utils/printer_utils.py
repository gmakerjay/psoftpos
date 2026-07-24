# -*- coding: utf-8 -*-
"""
Printer Utils - ระบบพิมพ์ใบเสร็จอัจฉริยะ
รองรับทุกประเภทเครื่องพิมพ์:
  - Thermal (ESC/POS: 58mm, 80mm) → พิมพ์ตรง ไม่เปิด PDF
  - Windows Printer (A4, A5) → พิมพ์เงียบผ่าน win32api
  - Label Printer (Xprinter TSPL) → ส่งคำสั่ง RAW
  - PDF → บันทึกไฟล์ + เปิดเฉพาะ A4
"""

import os
import subprocess
import platform
import threading
import time
from pathlib import Path
from datetime import datetime
from config import COMPANY_INFO


class PrinterManager:
    """จัดการการพิมพ์ใบเสร็จ (รองรับ ESC/POS, TSPL, Windows, PDF)"""
    
    def __init__(self):
        self.printer_type = "thermal"  # pdf, windows, thermal
        self.paper_size = "58mm"       # A4, A5, 80mm, 58mm, label
        self.printer_name = "XP-58"    # ชื่อเครื่องพิมพ์
        self.printer_codepage = "18"   # รหัสภาษาไทยเครื่องพิมพ์
        self.printer_feed_lines = 8    # จำนวนบรรทัดส่งกระดาษก่อนตัด (เพิ่มระยะขอบสวยงาม ไม่ชิดเป๊ะเกินไป)
        self.load_settings()

    def log_debug(self, message):
        """บันทึก log การทำงานเพื่อ Debug"""
        try:
            with open("printer_debug.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def load_settings(self):
        """โหลดการตั้งค่าเครื่องพิมพ์จาก database"""
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            printer_type = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'printer_type'")
            paper_size = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'paper_size'")
            printer_name = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'printer_name'")
            printer_codepage = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'printer_codepage'")
            feed_lines = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'printer_feed_lines'")
            db.disconnect()
            
            if printer_type: self.printer_type = printer_type['setting_value']
            if paper_size: self.paper_size = paper_size['setting_value']
            if printer_name: self.printer_name = printer_name['setting_value']
            if printer_codepage: self.printer_codepage = printer_codepage['setting_value']
            if feed_lines:
                try:
                    self.printer_feed_lines = int(feed_lines['setting_value'].split()[0])
                except Exception:
                    pass
        except Exception as e:
            self.log_debug(f"Error loading settings: {e}")
    
    def print_receipt(self, receipt_data):
        """
        พิมพ์ใบเสร็จตามประเภทที่ตั้งค่าไว้
        - thermal → ESC/POS หรือ TSPL (พิมพ์ตรง ไม่เปิดอะไรเลย)
        - windows → สร้าง PDF แล้วสั่งพิมพ์เงียบ (ไม่เปิด PDF ยกเว้น A4)
        - pdf → บันทึกไฟล์ + เปิดเฉพาะ A4
        """
        self.log_debug(f"=== START print_receipt (Type: {self.printer_type}, Paper: {self.paper_size}, Printer: {self.printer_name}) ===")
        
        # แปลง sqlite3.Row → dict
        if hasattr(receipt_data, 'keys'):
            receipt_data = dict(receipt_data)
        
        if 'items' in receipt_data and isinstance(receipt_data['items'], list):
            new_items = []
            for item in receipt_data['items']:
                item_dict = dict(item) if hasattr(item, 'keys') else item
                if 'total_price' not in item_dict and 'total' in item_dict:
                    item_dict['total_price'] = item_dict['total']
                if 'unit_price' not in item_dict and 'price' in item_dict:
                    item_dict['unit_price'] = item_dict['price']
                new_items.append(item_dict)
            receipt_data['items'] = new_items

        try:
            # Safety: ตรวจจับเครื่องพิมพ์ thermal ที่ตั้งค่าผิดเป็นโหมด windows (GDI)
            # GDI ไม่รองรับ font ภาษาไทยบนเครื่อง thermal → ตัวอักษรเพี้ยน (mojibake)
            # แก้ปัญหาซ้ำๆ โดยบังคับใช้ ESC/POS เมื่อตรวจพบเครื่อง thermal
            thermal_keywords = ["XP-58", "XP-80", "XP58", "XP80", "POS-58", "POS-80", "POS58", "POS80"]
            is_thermal_printer = self.printer_name and any(kw.lower() in self.printer_name.lower() for kw in thermal_keywords)
            
            if is_thermal_printer and self.printer_type == "windows":
                self.log_debug(f"⚠️ Auto-redirect: Printer '{self.printer_name}' is thermal but configured as 'windows'. Switching to ESC/POS to fix Thai encoding.")
                self.printer_type = "thermal"  # แก้ไขชั่วคราวในหน่วยความจำ (ไม่เขียนกลับ DB)
            
            if self.printer_type == "thermal":
                # Thermal → ส่ง RAW โดยตรง (ไม่เปิด PDF)
                if self.printer_name and "Xprinter" in self.printer_name:
                    return self.print_tspl_label(receipt_data)
                else:
                    return self.print_thermal_escpos(receipt_data)
                    
            elif self.printer_type == "windows":
                # Windows Printer → สร้าง PDF แล้วสั่งพิมพ์เงียบ
                return self.print_windows_silent(receipt_data)
                
            else:
                # PDF mode → บันทึกไฟล์ เปิดเฉพาะ A4
                return self.print_as_pdf(receipt_data)
                
        except Exception as e:
            self.log_debug(f"Critical error in print: {e}")
            return False

    # =====================================================
    # Thermal Printer (ESC/POS) — สั่งพิมพ์ตรง ไม่เปิด Window
    # =====================================================
    
    def print_thermal_escpos(self, receipt_data):
        """พิมพ์ตรง ESC/POS สำหรับเครื่องพิมพ์สลิป 58mm/80mm — ใช้ Bitmap Rendering (รองรับภาษาไทย 100%)"""
        try:
            commands = self.generate_bitmap_receipt(receipt_data)
            result = self.send_raw_to_printer(commands)
            self.log_debug(f"ESC/POS Bitmap print result: {result}")
            return result
        except Exception as e:
            self.log_debug(f"ESC/POS Bitmap Error: {e}")
            import traceback
            self.log_debug(traceback.format_exc())
            return False

    # =====================================================
    # Bitmap Receipt Rendering — แปลงใบเสร็จเป็นรูปภาพ
    # รองรับภาษาไทย 100% โดยไม่พึ่ง Thai font ROM ในเครื่องพิมพ์
    # =====================================================

    def _get_thai_font(self, size):
        """โหลดฟอนต์ภาษาไทยสำหรับ render bitmap"""
        from PIL import ImageFont
        from pathlib import Path
        
        base_dir = Path(__file__).resolve().parent.parent
        font_paths = [
            base_dir / "FC Sara Samkan [Non-commercial] Bold.ttf",
            base_dir / "assets" / "FC Sara Samkan [Non-commercial] Bold.ttf",
        ]
        
        for fp in font_paths:
            if fp.exists():
                return ImageFont.truetype(str(fp), size)
        
        # Fallback: ใช้ฟอนต์ที่ติดตั้งในระบบ
        for fallback in ["Tahoma", "Angsana New", "Cordia New", "TH Sarabun New", "Arial"]:
            try:
                return ImageFont.truetype(fallback, size)
            except Exception:
                continue
        
        # Last resort
        return ImageFont.load_default()

    def _render_receipt_image(self, receipt_data):
        """Render ใบเสร็จเป็น PIL Image ขาวดำ"""
        from PIL import Image, ImageDraw
        
        paper_width = 384 if self.paper_size == "58mm" else 576  # dots (203 DPI)
        
        font_size = 18 if self.paper_size == "58mm" else 22
        font = self._get_thai_font(font_size)
        font_bold = self._get_thai_font(font_size + 4)
        font_small = self._get_thai_font(font_size - 4)
        
        line_h = font_size + 8
        bold_h = font_size + 14
        sep_char = '-'
        
        # ดึงการตั้งค่าจาก Database
        company_name = "ชื่อร้านค้า"
        receipt_message = "ขอบคุณที่ใช้บริการ\nยินดีให้บริการ"
        show_cashier = True
        
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            
            name_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'company_name'")
            if name_setting and name_setting['setting_value'].strip():
                company_name = name_setting['setting_value']
                
            msg_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'receipt_message'")
            if msg_setting and msg_setting['setting_value'].strip():
                receipt_message = msg_setting['setting_value']
                
            cashier_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'receipt_show_cashier'")
            if cashier_setting:
                show_cashier = cashier_setting['setting_value'] == 'True'
                
            db.disconnect()
        except Exception:
            company_name = COMPANY_INFO.get('name', 'ชื่อร้านค้า')
        
        # === สร้างรายการบรรทัดที่จะพิมพ์ ===
        # แต่ละบรรทัดเป็น tuple: (text, font, align, left_right_pair)
        # align: 'left', 'center', 'right', 'lr' (left-right split)
        draw_ops = []
        
        def add_center(text, f=None):
            draw_ops.append(('center', text, f or font, None))
        def add_left(text, f=None):
            draw_ops.append(('left', text, f or font, None))
        def add_lr(left, right, f=None):
            draw_ops.append(('lr', left, f or font, right))
        def add_separator():
            draw_ops.append(('sep', None, font, None))
        
        # ชื่อร้าน
        add_center(company_name, font_bold)
        
        # ข้อมูลบิล
        add_left(f"เลขที่: {receipt_data['sale_number']}")
        add_left(f"วันที่: {receipt_data.get('sale_date', '-')}")
        cashier = receipt_data.get('cashier', '-')
        if show_cashier and cashier and cashier != '-':
            add_left(f"พนักงาน: {cashier}")
        
        cust_name = receipt_data.get('customer_name')
        if cust_name:
            add_left(f"สมาชิก: {cust_name}")
            
        add_separator()
        
        # รายการสินค้า
        for item in receipt_data.get('items', []):
            name = item.get('product_name', 'Item')
            add_left(name)
            
            qty = item.get('quantity', 0)
            price = item.get('unit_price', 0)
            total = item.get('total_price', 0)
            detail = f"  {qty} x {price:,.2f}"
            total_str = f"{total:,.2f}"
            add_lr(detail, total_str)
        
        add_separator()
        
        # สรุปยอด
        subtotal = receipt_data.get('subtotal', receipt_data.get('total_amount', 0))
        discount = receipt_data.get('discount_amount', 0)
        tax = receipt_data.get('tax_amount', 0)
        total = receipt_data.get('total_amount', 0)
        paid = receipt_data.get('paid_amount', 0)
        change = receipt_data.get('change_amount', 0)
        
        if discount > 0:
            add_lr("ยอดรวม:", f"{subtotal:,.2f}")
            add_lr("ส่วนลด:", f"{discount:,.2f}")
        if tax > 0:
            add_lr("ภาษี VAT:", f"{tax:,.2f}")
        
        add_lr("ยอดสุทธิ:", f"{total:,.2f}", font_bold)
        add_separator()
        add_lr("รับเงิน:", f"{paid:,.2f}")
        add_lr("เงินทอน:", f"{change:,.2f}")
        
        # Footer
        draw_ops.append(('blank', None, font, None))
        for msg_line in receipt_message.split('\n'):
            add_center(msg_line)
            
        # วาดรูป QR Code ท้ายใบเสร็จ
        try:
            from database import DatabaseManager
            db = DatabaseManager()
            db.connect()
            qr_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
            db.disconnect()
            if qr_setting and qr_setting['setting_value'].strip():
                qr_path = qr_setting['setting_value'].strip()
                if os.path.exists(qr_path):
                    from PIL import Image
                    qr_img = Image.open(qr_path).convert("1")
                    # ปรับขนาดตามหน้ากระดาษ (ประมาณ 40% ของพื้นที่กระดาษ)
                    target_w = int(paper_width * 0.4)
                    qr_img = qr_img.resize((target_w, target_w), Image.Resampling.LANCZOS)
                    draw_ops.append(('blank', None, font, None))
                    draw_ops.append(('image', qr_img, font, None))
        except Exception as e:
            self.log_debug(f"Error loading QR Code for ESC/POS: {e}")
        
        # === คำนวณความสูงรวม ===
        total_height = 15  # top padding
        for op_type, text, f, _ in draw_ops:
            if op_type == 'blank':
                total_height += line_h // 2
            elif op_type == 'sep':
                total_height += line_h
            elif op_type == 'image':
                img_w, img_h = text.size
                total_height += img_h
            elif f == font_bold:
                total_height += bold_h
            else:
                total_height += line_h
        total_height += 100  # bottom padding (เพิ่มระยะเผื่อขอบล่างให้กระดาษส่งพ้นใบมีดตัดแบบสวยงาม)
        
        # === วาดภาพ ===
        img = Image.new('1', (paper_width, total_height), 1)  # 1 = white
        draw = ImageDraw.Draw(img)
        
        y = 10
        for op_type, text, f, extra in draw_ops:
            if op_type == 'blank':
                y += line_h // 2
                continue
            
            if op_type == 'sep':
                # วาดเส้นประ
                bbox = f.getbbox(sep_char)
                char_w = bbox[2] - bbox[0] if bbox else 6
                num_chars = paper_width // char_w
                draw.text((0, y), sep_char * num_chars, font=f, fill=0)
                y += line_h
                continue
            
            h = bold_h if f == font_bold else line_h
            
            if op_type == 'center':
                bbox = f.getbbox(text)
                tw = (bbox[2] - bbox[0]) if bbox else 0
                x = max(0, (paper_width - tw) // 2)
                draw.text((x, y), text, font=f, fill=0)
            
            elif op_type == 'left':
                draw.text((3, y), text, font=f, fill=0)
            
            elif op_type == 'lr':
                # ซ้าย
                draw.text((3, y), text, font=f, fill=0)
                # ขวา
                right_text = extra
                bbox = f.getbbox(right_text)
                rw = (bbox[2] - bbox[0]) if bbox else 0
                draw.text((paper_width - rw - 3, y), right_text, font=f, fill=0)
                
            elif op_type == 'image':
                img_w, img_h = text.size
                x = max(0, (paper_width - img_w) // 2)
                img.paste(text, (x, y))
                y += img_h
                continue
            
            y += h
        
        return img

    def _image_to_escpos_raster(self, img):
        """แปลง PIL Image (1-bit) เป็นคำสั่ง ESC/POS raster (GS v 0)"""
        from PIL import Image
        img = img.convert('1')
        width, height = img.size
        
        width_bytes = (width + 7) // 8
        
        commands = bytearray()
        
        # GS v 0 m xL xH yL yH d1...dk
        m = 0  # normal density
        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF
        yL = height & 0xFF
        yH = (height >> 8) & 0xFF
        
        commands += b'\x1d\x76\x30'  # GS v 0
        commands += bytes([m, xL, xH, yL, yH])
        
        pixels = img.load()
        for row in range(height):
            row_data = bytearray(width_bytes)
            for col in range(width):
                if pixels[col, row] == 0:  # black pixel
                    byte_idx = col // 8
                    bit_idx = 7 - (col % 8)
                    row_data[byte_idx] |= (1 << bit_idx)
            commands += bytes(row_data)
        
        return bytes(commands)

    def generate_bitmap_receipt(self, receipt_data):
        """สร้างคำสั่ง ESC/POS แบบ Bitmap สำหรับใบเสร็จ (รองรับภาษาไทย 100%)"""
        GS = b'\x1d'
        ESC = b'\x1b'
        
        commands = bytearray()
        
        # Initialize printer
        commands += ESC + b'@'  # ESC @
        
        # Render ใบเสร็จเป็นรูปภาพ
        img = self._render_receipt_image(receipt_data)
        self.log_debug(f"Bitmap receipt rendered: {img.size[0]}x{img.size[1]} pixels")
        
        # แปลงเป็น raster commands
        commands += self._image_to_escpos_raster(img)
        
        # Feed + Cut (ส่งกระดาษพ้นหัวตัดก่อนสั่งตัด 8 บรรทัด ให้มีระยะขอบสวยงามไม่ชิดเป๊ะเกินไป)
        feed_lines = max(5, int(getattr(self, 'printer_feed_lines', 8)))
        commands += ESC + b'd' + bytes([feed_lines])  # ESC d n (Feed n lines)
        commands += GS + b'V\x42\x00'                 # GS V 66 0 (Feed and full cut)
        
        return bytes(commands)

    def send_raw_to_printer(self, data):
        """ส่งข้อมูลดิบไป Windows Spooler (สำหรับ thermal/label)"""
        try:
            import win32print
            p_name = self.printer_name if self.printer_name else win32print.GetDefaultPrinter()
            self.log_debug(f"Sending RAW data to: {p_name} ({len(data)} bytes)")
            
            hPrinter = win32print.OpenPrinter(p_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS_Receipt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                self.log_debug("RAW print sent successfully")
            finally:
                win32print.ClosePrinter(hPrinter)
            return True
        except ImportError:
            self.log_debug("win32print not available — cannot send raw data")
            return False
        except Exception as e:
            self.log_debug(f"Raw Send Error: {e}")
            return False

    def open_cash_drawer(self):
        """
        เปิดลิ้นชักเงินสด (Cash Drawer Kick)
        
        ใช้คำสั่ง ESC/POS มาตรฐาน — Universal สำหรับลิ้นชักทุกยี่ห้อ
        ที่ต่อผ่านเครื่องพิมพ์ใบเสร็จ (RJ11/RJ12)
        
        คำสั่ง ESC p m t1 t2:
        - m=0: Pin 2 (ลิ้นชักช่อง 1 — ทั่วไป)
        - m=1: Pin 5 (ลิ้นชักช่อง 2 — บางรุ่น)
        - t1=25: Pulse ON 50ms
        - t2=250: Pulse OFF 500ms
        
        รองรับ: Epson, XPrinter, Bixolon, Star, SUNMI, Rongta, 
                 HOIN, MHT, Zjiang, และเครื่องพิมพ์ ESC/POS ทุกรุ่น
        """
        try:
            # คำสั่งเปิดลิ้นชัก — ส่งทั้ง 2 Pin เพื่อรองรับทุกการต่อสาย
            drawer_commands = bytearray()
            
            # Pin 2 (Connector 1) — ใช้มากที่สุด
            drawer_commands += b'\x1b\x70\x00\x19\xfa'
            
            # Pin 5 (Connector 2) — สำหรับลิ้นชักที่ต่อ Pin 5
            drawer_commands += b'\x1b\x70\x01\x19\xfa'
            
            success = self.send_raw_to_printer(bytes(drawer_commands))
            
            if success:
                self.log_debug("Cash drawer opened successfully (ESC p — Pin 2 + Pin 5)")
            else:
                self.log_debug("Cash drawer: send_raw_to_printer failed — trying fallback")
                # Fallback: ลองส่งผ่าน win32print โดยตรง
                success = self._open_drawer_win32()
            
            return success
            
        except Exception as e:
            self.log_debug(f"Cash Drawer Error: {e}")
            return False
    
    def _open_drawer_win32(self):
        """Fallback — ส่งคำสั่งเปิดลิ้นชักผ่าน win32print โดยตรง"""
        try:
            import win32print
            p_name = self.printer_name if self.printer_name else win32print.GetDefaultPrinter()
            
            kick_data = b'\x1b\x70\x00\x19\xfa' + b'\x1b\x70\x01\x19\xfa'
            
            hPrinter = win32print.OpenPrinter(p_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("CashDrawerKick", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, kick_data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                self.log_debug(f"Cash drawer opened via win32print fallback: {p_name}")
            finally:
                win32print.ClosePrinter(hPrinter)
            return True
        except Exception as e:
            self.log_debug(f"Cash Drawer win32 fallback error: {e}")
            return False

    # =====================================================
    # Windows Printer — สร้าง PDF แล้วสั่งพิมพ์เงียบ
    # =====================================================

    def print_windows_silent(self, receipt_data):
        """
        พิมพ์ผ่าน Windows Printer:
        - ขนาด A4 → เปิด PDF ให้ user ดู/สั่งพิมพ์เอง
        - ขนาดอื่น (80mm, 58mm, A5) → สั่งพิมพ์เงียบ ไม่เปิดอะไร (ใช้ GDI)
        """
        try:
            from utils.pdf_utils import create_receipt_pdf
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / f"tmp_print_{receipt_data['sale_number']}.pdf"
            
            if not create_receipt_pdf(receipt_data, str(temp_file), paper_size=self.paper_size):
                self.log_debug("Failed to create PDF for printing")
                return False
            
            if platform.system() != 'Windows':
                self.log_debug("Not Windows, opening PDF")
                os.startfile(str(temp_file))
                return True
            
            # === A4: เปิด PDF Viewer ให้ user สั่งพิมพ์เอง ===
            if self.paper_size == "A4":
                self.log_debug("A4 mode: opening PDF viewer")
                os.startfile(str(temp_file))
                return True
            
            # === ขนาดอื่น: ลองพิมพ์ผ่าน GDI (พิมพ์เงียบ ครอบจักรวาล) ===
            self.log_debug(f"Paper size is {self.paper_size}. Routing to GDI Print.")
            if self.print_via_gdi(receipt_data):
                return True
                
            self.log_debug("GDI Print failed, falling back to standard PDF silent printing methods")
            
            # === ขนาดอื่น: พิมพ์เงียบ ไม่เปิด Window (Fallback) ===
            p_name = self._get_printer_name()
            
            # วิธี 1: win32api.ShellExecute — เงียบที่สุด
            if self._print_via_shellexecute(str(temp_file), p_name):
                return True
            
            # วิธี 2: PowerShell + SumatraPDF (ถ้ามี)
            if self._print_via_sumatra(str(temp_file), p_name):
                return True
            
            # วิธี 3: PowerShell Out-Printer
            if self._print_via_powershell(str(temp_file), p_name):
                return True
            
            # วิธี 4 (สุดท้าย): เปิด PDF ให้ user กดพิมพ์เอง
            self.log_debug("All silent methods failed, falling back to os.startfile")
            os.startfile(str(temp_file), "print")
            return True
            
        except Exception as e:
            self.log_debug(f"WinPrint Error: {e}")
            return False

    def print_via_gdi(self, receipt_data):
        """พิมพ์ตรงไปเครื่องพิมพ์ผ่าน GDI (รองรับภาษาไทย 100% และทุกเครื่องพิมพ์ในโลกหลังลงไดรเวอร์)"""
        try:
            import win32print
            import win32ui
            import win32con
            
            p_name = self._get_printer_name()
            if not p_name:
                self.log_debug("GDI Print: No printer found")
                return False
                
            self.log_debug(f"GDI Print: Sending job to '{p_name}'")
            
            # ดึงข้อความท้ายใบเสร็จจากตาราง settings
            receipt_message = "ขอบคุณที่ใช้บริการ\nยินดีให้บริการ"
            try:
                from database import DatabaseManager
                db = DatabaseManager()
                db.connect()
                receipt_msg_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'receipt_message'")
                db.disconnect()
                if receipt_msg_setting and receipt_msg_setting['setting_value'].strip():
                    receipt_message = receipt_msg_setting['setting_value']
            except Exception as e:
                self.log_debug(f"Error loading receipt message for GDI: {e}")

            # ดึงการตั้งค่าพนักงานและบาร์โค้ดจาก settings
            show_cashier = True
            try:
                db = DatabaseManager()
                db.connect()
                show_cashier_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'receipt_show_cashier'")
                db.disconnect()
                if show_cashier_setting:
                    show_cashier = show_cashier_setting['setting_value'] == 'True'
            except Exception:
                pass

            # คำนวณขนาดกระดาษและฟอนต์ที่ใช้พิมพ์
            paper_size = self.paper_size
            if paper_size == "58mm":
                width_mm = 58          # ขนาดความกว้างกระดาษจริง
                print_width_mm = 48    # พื้นที่พิมพ์ได้จริง
                font_sz = 8
                title_sz = 11
            elif paper_size == "A5":
                width_mm = 148
                print_width_mm = 138
                font_sz = 11
                title_sz = 15
            elif paper_size == "A4":
                width_mm = 210
                print_width_mm = 190
                font_sz = 12
                title_sz = 18
            else: # 80mm หรือค่าเริ่มต้น
                width_mm = 80          # ขนาดความกว้างกระดาษจริง
                print_width_mm = 72    # พื้นที่พิมพ์ได้จริง
                font_sz = 10
                title_sz = 14

            # คำนวณความสูงกระดาษที่ใช้จริง (หน่วย mm) เพื่อกำหนดขนาดหน้ากระดาษแบบไดนามิก
            # ป้องกันกระดาษไหลเปล่ายาวมากหลังพิมพ์เสร็จในระบบ Windows GDI
            num_items = len(receipt_data.get('items', []))
            estimated_height_mm = 90 + (num_items * 8) # ความสูงพื้นฐาน + จำนวนสินค้า
            
            # เพิ่มระยะเผื่อตัวเลือกอื่นๆ
            if receipt_data.get('discount_amount', 0) > 0:
                estimated_height_mm += 10
            if receipt_data.get('tax_amount', 0) > 0:
                estimated_height_mm += 10
            estimated_height_mm += len(receipt_message.split('\n')) * 5 # ข้อความท้ายบิล
            estimated_height_mm += 15 # เผื่อช่องฉีก/ระยะตัด (Margin ล่าง)

            if estimated_height_mm < 100:
                estimated_height_mm = 100 # ขั้นต่ำ 10cm เพื่อป้องกันกระดาษขาดช่วง

            # ดึง DEVMODE ของเครื่องพิมพ์มาปรับแต่งขนาดกระดาษ
            devmode = None
            hprinter = None
            try:
                import win32print
                import win32con
                
                hprinter = win32print.OpenPrinter(p_name)
                # ดึงโครงสร้างข้อมูลระดับ 2 ซึ่งประกอบด้วย DEVMODE
                info = win32print.GetPrinter(hprinter, 2)
                devmode = info['pDevMode']
                
                if devmode:
                    devmode.PaperSize = 0  # 0 หมายถึงกำหนดขนาดกระดาษเอง (User defined)
                    devmode.PaperWidth = int(width_mm * 10)     # หน่วย 0.1 มม.
                    devmode.PaperLength = int(estimated_height_mm * 10)  # หน่วย 0.1 มม.
                    devmode.Fields = devmode.Fields | win32con.DM_PAPERSIZE | win32con.DM_PAPERWIDTH | win32con.DM_PAPERLENGTH
            except Exception as e:
                self.log_debug(f"GDI Print: Cannot customize DEVMODE (Fallback to defaults): {e}")
            finally:
                if hprinter:
                    try:
                        win32print.ClosePrinter(hprinter)
                    except Exception:
                        pass

            # เตรียม Device Context
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(p_name)
            
            hdc.StartDoc("POS Receipt " + receipt_data.get('sale_number', ''))
            hdc.StartPage()
            
            dpi_x = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
            dpi_y = hdc.GetDeviceCaps(win32con.LOGPIXELSY)
            
            page_width = int((print_width_mm / 25.4) * dpi_x)
            
            # โหลดฟอนต์ภาษาไทยของโปรเจกต์ชั่วคราวเพื่อให้ GDI เรียกใช้ได้โดยไม่ต้องติดตั้งลง Windows
            font_name = "Tahoma"
            try:
                import ctypes
                from pathlib import Path
                base_dir = Path(__file__).resolve().parent.parent
                font_path = base_dir / "FC Sara Samkan [Non-commercial] Bold.ttf"
                if font_path.exists():
                    ctypes.windll.gdi32.AddFontResourceW(str(font_path))
                    font_name = "FC Sara Samkan"
            except Exception as e:
                self.log_debug(f"GDI Print: Cannot load custom font resource: {e}")

            # สร้างฟอนต์
            font_title = win32ui.CreateFont({
                'name': font_name,
                'height': int(title_sz * dpi_y / 72),
                'weight': 700,
            })
            font_body = win32ui.CreateFont({
                'name': font_name,
                'height': int(font_sz * dpi_y / 72),
                'weight': 400,
            })
            font_bold = win32ui.CreateFont({
                'name': font_name,
                'height': int(font_sz * dpi_y / 72),
                'weight': 700,
            })
            
            y = 10
            
            def draw_centered(text, font):
                nonlocal y
                hdc.SelectObject(font)
                w, h = hdc.GetTextExtent(text)
                hdc.TextOut((page_width - w) // 2, y, text)
                y += h + int(2 * dpi_y / 72)
                
            def draw_left_right(left, right, font, bold_right=False):
                nonlocal y
                hdc.SelectObject(font)
                hdc.TextOut(0, y, left)
                if bold_right:
                    hdc.SelectObject(font_bold)
                w, h = hdc.GetTextExtent(right)
                hdc.TextOut(page_width - w, y, right)
                y += h + int(2 * dpi_y / 72)
                
            def draw_separator():
                nonlocal y
                hdc.SelectObject(font_body)
                char_w, h = hdc.GetTextExtent("-")
                num_chars = page_width // char_w
                hdc.TextOut(0, y, "-" * num_chars)
                y += h + int(2 * dpi_y / 72)
                
            def wrap_text(text, max_w, font):
                hdc.SelectObject(font)
                lines = []
                current = ""
                for char in text:
                    test = current + char
                    w, _ = hdc.GetTextExtent(test)
                    if w > max_w:
                        lines.append(current)
                        current = char
                    else:
                        current = test
                if current:
                    lines.append(current)
                return lines
                
            company_info = receipt_data.get('company', COMPANY_INFO)
            
            # 1. ชื่อร้าน
            draw_centered(company_info.get('name', 'ชื่อร้านค้า'), font_title)
            
            # 2. ที่อยู่
            address = company_info.get('address', '')
            if address:
                addr_lines = wrap_text(address, page_width, font_body)
                for line in addr_lines:
                    draw_centered(line, font_body)
                    
            # เบอร์โทรศัพท์ และเลขผู้เสียภาษี
            phone = company_info.get('phone', '')
            if phone:
                draw_centered("โทร: " + phone, font_body)
            tax_id = company_info.get('tax_id', '')
            if tax_id:
                draw_centered("เลขผู้เสียภาษี: " + tax_id, font_body)
                
            y += int(5 * dpi_y / 72)
            
            # 3. เลขที่และเวลา
            draw_left_right("เลขที่: " + receipt_data.get('sale_number', '-'), "", font_body)
            draw_left_right("วันที่: " + receipt_data.get('sale_date', '-'), "", font_body)
            cashier = receipt_data.get('cashier', '-')
            if show_cashier and cashier and cashier != '-':
                draw_left_right("พนักงาน: " + cashier, "", font_body)
                
            cust_name = receipt_data.get('customer_name')
            if cust_name:
                draw_left_right("สมาชิก: " + cust_name, "", font_body)
                
            draw_separator()
            
            # 4. รายการสินค้า
            for item in receipt_data.get('items', []):
                name = item.get('product_name', '')
                qty = item.get('quantity', 0)
                price = item.get('unit_price', 0)
                total = item.get('total_price', 0)
                
                # ตัดคำชื่อสินค้า โดยให้กว้างสุด 65% ของหน้ากระดาษ
                name_max_w = int(page_width * 0.65)
                name_lines = wrap_text(name, name_max_w, font_body)
                
                # วาดบรรทัดแรก
                hdc.SelectObject(font_body)
                hdc.TextOut(0, y, name_lines[0])
                
                # วาดราคาและยอดรวมในบรรทัดเดียวกัน
                price_str = f"{qty} x {price:,.2f}"
                total_str = f"{total:,.2f}"
                
                total_w, h = hdc.GetTextExtent(total_str)
                hdc.TextOut(page_width - total_w, y, total_str)
                
                price_w, _ = hdc.GetTextExtent(price_str)
                hdc.TextOut(page_width - total_w - price_w - int(10 * dpi_x / 72), y, price_str)
                
                y += h + int(2 * dpi_y / 72)
                
                # วาดส่วนของชื่อสินค้าที่ยาวเกินในบรรทัดถัดไป
                for extra_line in name_lines[1:]:
                    hdc.SelectObject(font_body)
                    hdc.TextOut(0, y, extra_line)
                    y += h + int(2 * dpi_y / 72)
                    
            draw_separator()
            
            # 5. ยอดรวมเงิน
            subtotal = receipt_data.get('subtotal', 0)
            discount = receipt_data.get('discount_amount', 0)
            tax = receipt_data.get('tax_amount', 0)
            total_amount = receipt_data.get('total_amount', 0)
            paid = receipt_data.get('paid_amount', 0)
            change = receipt_data.get('change_amount', 0)
            
            if discount > 0:
                draw_left_right("ยอดรวม:", f"{subtotal:,.2f}", font_body)
                draw_left_right("ส่วนลด:", f"{discount:,.2f}", font_body)
            if tax > 0:
                draw_left_right("ภาษี VAT:", f"{tax:,.2f}", font_body)
                
            draw_left_right("ยอดสุทธิ:", f"{total_amount:,.2f}", font_bold, bold_right=True)
            draw_separator()
            
            draw_left_right("รับเงิน:", f"{paid:,.2f}", font_body)
            draw_left_right("เงินทอน:", f"{change:,.2f}", font_bold, bold_right=True)
            
            draw_separator()
            
            # 6. ข้อความท้ายบิล
            for line in receipt_message.split('\n'):
                draw_centered(line, font_body)
                
            # วาดรูป QR Code ท้ายใบเสร็จในระบบ GDI
            try:
                from database import DatabaseManager
                db = DatabaseManager()
                db.connect()
                qr_setting = db.fetch_one("SELECT setting_value FROM settings WHERE setting_key = 'payment_qr_path'")
                db.disconnect()
                if qr_setting and qr_setting['setting_value'].strip():
                    qr_path = qr_setting['setting_value'].strip()
                    if os.path.exists(qr_path):
                        from PIL import Image, ImageWin
                        qr_img = Image.open(qr_path).convert("L")
                        target_w = int(page_width * 0.4)
                        qr_img = qr_img.resize((target_w, target_w), Image.Resampling.LANCZOS)
                        
                        dib = ImageWin.Dib(qr_img)
                        x_pos = (page_width - target_w) // 2
                        y += int(10 * dpi_y / 72)
                        dib.draw(hdc.GetSafeHdc(), (x_pos, y, x_pos + target_w, y + target_w))
                        y += target_w + int(10 * dpi_y / 72)
            except Exception as e:
                self.log_debug(f"GDI Print: Error printing QR Code image: {e}")
                
            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()
            
            self.log_debug("GDI Print: Job sent successfully")
            return True
            
        except Exception as e:
            self.log_debug(f"GDI Print Error: {e}")
            import traceback
            self.log_debug(traceback.format_exc())
            return False
    
    def _get_printer_name(self):
        """หาชื่อเครื่องพิมพ์ที่จะใช้"""
        if self.printer_name and self.printer_name not in ["ไม่พบเครื่องพิมพ์", "เกิดข้อผิดพลาด", ""]:
            return self.printer_name
        try:
            import win32print
            return win32print.GetDefaultPrinter()
        except Exception:
            return None
    
    def _print_via_shellexecute(self, filepath, printer_name):
        """พิมพ์ผ่าน win32api.ShellExecute — เงียบที่สุด"""
        try:
            import win32api
            self.log_debug(f"Trying ShellExecute print: {printer_name}")
            # "print" verb จะสั่งพิมพ์โดยไม่เปิด viewer
            win32api.ShellExecute(0, "print", filepath, f'/d:"{printer_name}"' if printer_name else None, ".", 0)
            self.log_debug("ShellExecute print sent")
            return True
        except ImportError:
            self.log_debug("win32api not available")
            return False
        except Exception as e:
            self.log_debug(f"ShellExecute error: {e}")
            return False
    
    def _print_via_sumatra(self, filepath, printer_name):
        """พิมพ์ผ่าน SumatraPDF (ถ้าติดตั้ง) — เงียบ 100%"""
        try:
            sumatra_paths = [
                r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
                os.path.expanduser(r"~\AppData\Local\SumatraPDF\SumatraPDF.exe"),
            ]
            for spath in sumatra_paths:
                if os.path.exists(spath):
                    self.log_debug(f"Trying SumatraPDF: {spath}")
                    cmd = [spath, "-print-to", printer_name or "default", "-silent", filepath]
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.log_debug("SumatraPDF print sent")
                    return True
        except Exception as e:
            self.log_debug(f"SumatraPDF error: {e}")
        return False
    
    def _print_via_powershell(self, filepath, printer_name):
        """พิมพ์ผ่าน PowerShell — plan C"""
        try:
            self.log_debug(f"Trying PowerShell print: {printer_name}")
            if printer_name:
                cmd = f'Start-Process -FilePath "{filepath}" -Verb PrintTo -ArgumentList "{printer_name}" -WindowStyle Hidden'
            else:
                cmd = f'Start-Process -FilePath "{filepath}" -Verb Print -WindowStyle Hidden'
            
            result = subprocess.run(
                ['powershell', '-WindowStyle', 'Hidden', '-Command', cmd],
                capture_output=True, timeout=15
            )
            self.log_debug(f"PowerShell result: returncode={result.returncode}")
            return result.returncode == 0
        except Exception as e:
            self.log_debug(f"PowerShell error: {e}")
            return False

    # =====================================================
    # PDF Mode — บันทึกไฟล์
    # =====================================================

    def print_as_pdf(self, receipt_data):
        """สร้าง PDF สำหรับเก็บไว้ในเครื่อง + เปิดเฉพาะ A4"""
        try:
            from utils.pdf_utils import create_receipt_pdf
            receipts_dir = Path("data/receipts")
            receipts_dir.mkdir(parents=True, exist_ok=True)
            filename = receipts_dir / f"receipt_{receipt_data['sale_number']}.pdf"
            
            result = create_receipt_pdf(receipt_data, str(filename), paper_size=self.paper_size)
            
            if result and self.paper_size == "A4":
                # เปิด PDF Viewer เฉพาะ A4
                self.log_debug("PDF saved, opening for A4")
                os.startfile(str(filename))
            elif result:
                self.log_debug(f"PDF saved silently: {filename}")
            
            return result
        except Exception as e:
            self.log_debug(f"PDF Error: {e}")
            return False

    # =====================================================
    # ตรวจหาเครื่องพิมพ์ในระบบ
    # =====================================================

    def get_available_printers(self):
        """ตรวจหาเครื่องพิมพ์ทั้งหมดในระบบ พร้อมสถานะ"""
        printers = []
        try:
            import win32print
            # ค้นหาทั้ง Local + Network printers
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            raw_printers = win32print.EnumPrinters(flags)
            
            for p in raw_printers:
                name = p[2]
                # กรอง printer ที่ไม่ใช่จริง
                skip_names = ["Microsoft XPS", "Microsoft Print to PDF", "Fax", "OneNote"]
                if any(skip in name for skip in skip_names):
                    continue
                printers.append(name)
            
            # ถ้ากรองหมดแล้วไม่เหลือ ให้เอากลับมาทั้งหมด
            if not printers:
                printers = [p[2] for p in raw_printers]
            
            # เพิ่ม Default printer ไว้ข้างบนสุด
            try:
                default = win32print.GetDefaultPrinter()
                if default in printers:
                    printers.remove(default)
                printers.insert(0, f"{default}")
            except Exception:
                pass
                
            self.log_debug(f"Found printers: {printers}")
            return printers if printers else ["ไม่พบเครื่องพิมพ์"]
            
        except ImportError:
            self.log_debug("win32print not installed — using fallback")
            # Fallback: ใช้ PowerShell ตรวจหา
            return self._get_printers_powershell()
        except Exception as e:
            self.log_debug(f"EnumPrinters error: {e}")
            return self._get_printers_powershell()
    
    def _get_printers_powershell(self):
        """ตรวจหาเครื่องพิมพ์ด้วย PowerShell (fallback)"""
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Printer | Select-Object -ExpandProperty Name'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                printers = [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
                self.log_debug(f"PowerShell found printers: {printers}")
                return printers if printers else ["ไม่พบเครื่องพิมพ์"]
        except Exception as e:
            self.log_debug(f"PowerShell printer detection error: {e}")
        return ["ไม่พบเครื่องพิมพ์"]
    
    def get_printer_info(self, printer_name):
        """ดึงข้อมูลรายละเอียดเครื่องพิมพ์"""
        try:
            import win32print
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                info = win32print.GetPrinter(hPrinter, 2)
                return {
                    'name': info['pPrinterName'],
                    'port': info['pPortName'],
                    'driver': info['pDriverName'],
                    'status': info['Status'],
                    'jobs': info['cJobs'],
                }
            finally:
                win32print.ClosePrinter(hPrinter)
        except Exception as e:
            self.log_debug(f"GetPrinterInfo error: {e}")
            return None


# =====================================================
# Global API — เรียกใช้จากที่อื่นโดยตรง
# =====================================================

def print_receipt(receipt_data, printer_type=None):
    """พิมพ์ใบเสร็จ (Global function)"""
    pm = PrinterManager()
    if printer_type:
        pm.printer_type = printer_type
    return pm.print_receipt(receipt_data)

def get_printers():
    """รายชื่อเครื่องพิมพ์ทั้งหมด"""
    return PrinterManager().get_available_printers()

def get_printer_details(name):
    """ข้อมูลเครื่องพิมพ์"""
    return PrinterManager().get_printer_info(name)

def kick_cash_drawer():
    """เปิดลิ้นชักเงินสด (Global function)"""
    return PrinterManager().open_cash_drawer()
