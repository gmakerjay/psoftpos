# -*- coding: utf-8 -*-
"""
หน้ารายงานยอดขาย — รวมข้อมูลจาก DB และ Backup .txt
ดึงข้อมูลจากทั้ง 2 แหล่ง เลือกช่วงวันที่ได้ แสดงรวมกัน + Export Excel
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from database import DatabaseManager
from config import *
from datetime import datetime, timedelta
from tkcalendar import DateEntry
from utils import SalesLogManager, ExcelManager
from pathlib import Path
import openpyxl
import re


class ReportsFrame(ctk.CTkFrame):
    """Frame สำหรับรายงานและวิเคราะห์ข้อมูล"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        self.slm = SalesLogManager()
        
        self.create_widgets()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text="📊 ระบบรายงานและวิเคราะห์ข้อมูล",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(side="left")
        
        # แท็บ
        self.tab_view = ctk.CTkTabview(self, corner_radius=10)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.tab_view.add("ยอดขายรวม")
        self.tab_view.add("ประวัติไฟล์ Backup")
        self.tab_view.add("สินค้าขายดี")
        self.tab_view.add("สินค้าใกล้หมดสต็อก")
        
        # จัดการเนื้อหาแต่ละแท็บ
        self.setup_sales_tab()
        self.setup_backup_tab()
        self.setup_best_selling_tab()
        self.setup_low_stock_tab()
        
        # ผูก event โหลดข้อมูลเมื่อเปลี่ยนแท็บ
        self.tab_view.configure(command=self.on_tab_changed)
        
        # โหลดแท็บแรก
        self.load_db_summary()

    # =====================================================
    # TAB 1: ยอดขายรวม (จาก DB — ข้อมูลที่ยังอยู่ในระบบ)
    # =====================================================
    def setup_sales_tab(self):
        tab = self.tab_view.tab("ยอดขายรวม")
        
        # ส่วนควบคุม (Filter + ปุ่ม)
        ctrl_frame = ctk.CTkFrame(tab, fg_color="white", corner_radius=10)
        ctrl_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # วันที่
        date_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        date_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(date_frame, text="จากวันที่:", font=FONTS["body"]).pack(side="left")
        self.start_date = DateEntry(date_frame, width=12, background=COLORS["primary"], date_pattern='dd/mm/yyyy')
        self.start_date.set_date(datetime.now() - timedelta(days=30))
        self.start_date.pack(side="left", padx=5)
        ctk.CTkLabel(date_frame, text="ถึง", font=FONTS["body"]).pack(side="left")
        self.end_date = DateEntry(date_frame, width=12, background=COLORS["primary"], date_pattern='dd/mm/yyyy')
        self.end_date.pack(side="left", padx=5)
        
        ctk.CTkButton(date_frame, text="🔍 ดึงข้อมูล", width=100, command=self.load_db_summary).pack(side="left", padx=10)
        
        # ปุ่มด้านขวา
        btn_right = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        btn_right.pack(side="right", padx=15, pady=10)
        
        ctk.CTkButton(
            btn_right,
            text="📥 Export Excel",
            fg_color=COLORS["success"],
            width=120,
            command=self.export_to_excel
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_right,
            text="🧹 ปิดยอดวัน",
            fg_color=COLORS["danger"],
            width=120,
            command=self.clear_daily_list
        ).pack(side="left", padx=5)
        
        # สถิติสรุป
        stats_frame = ctk.CTkFrame(tab, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.db_total_card = self._create_stat_card(stats_frame, "💰 ยอดขายรวม", "฿0.00", COLORS["success"])
        self.db_total_card.pack(side="left", fill="x", expand=True, padx=3)
        self.db_count_card = self._create_stat_card(stats_frame, "📝 จำนวนรายการ", "0", COLORS["info"])
        self.db_count_card.pack(side="left", fill="x", expand=True, padx=3)
        self.db_avg_card = self._create_stat_card(stats_frame, "📊 ยอดเฉลี่ย", "฿0.00", COLORS["warning"])
        self.db_avg_card.pack(side="left", fill="x", expand=True, padx=3)
        
        # ตารางข้อมูล
        self.db_summary_table = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        self.db_summary_table.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    # =====================================================
    # TAB 2: ประวัติไฟล์ Backup (จากไฟล์ .txt ที่เก็บถาวร)
    # =====================================================
    def setup_backup_tab(self):
        tab = self.tab_view.tab("ประวัติไฟล์ Backup")
        
        # ส่วนควบคุม
        ctrl_frame = ctk.CTkFrame(tab, fg_color="white", corner_radius=10)
        ctrl_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        date_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        date_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(date_frame, text="ช่วงวันที่:", font=FONTS["body"]).pack(side="left")
        self.backup_start_date = DateEntry(date_frame, width=12, background=COLORS["primary"], date_pattern='dd/mm/yyyy')
        self.backup_start_date.set_date(datetime.now() - timedelta(days=30))
        self.backup_start_date.pack(side="left", padx=5)
        ctk.CTkLabel(date_frame, text="ถึง", font=FONTS["body"]).pack(side="left")
        self.backup_end_date = DateEntry(date_frame, width=12, background=COLORS["primary"], date_pattern='dd/mm/yyyy')
        self.backup_end_date.pack(side="left", padx=5)
        
        ctk.CTkButton(date_frame, text="🔍 ดึงข้อมูลจากไฟล์ Backup", width=180, 
                       fg_color=COLORS["secondary"], command=self.load_backup_by_date).pack(side="left", padx=10)
        
        # Dropdown เลือกไฟล์
        file_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        file_frame.pack(side="right", padx=15, pady=10)
        
        ctk.CTkLabel(file_frame, text="หรือเลือกไฟล์:", font=FONTS["small"]).pack(side="left")
        self.backup_file_var = ctk.StringVar(value="-- ทั้งหมด --")
        self.backup_file_combo = ctk.CTkComboBox(
            file_frame,
            variable=self.backup_file_var,
            values=self._get_backup_files(),
            width=300,
            font=("Courier New", 11),
            command=lambda _: self.load_single_backup_file()
        )
        self.backup_file_combo.pack(side="left", padx=5)
        
        # สถิติจาก backup
        backup_stats = ctk.CTkFrame(tab, fg_color="transparent")
        backup_stats.pack(fill="x", padx=10, pady=5)
        
        self.backup_total_card = self._create_stat_card(backup_stats, "💰 ยอดรวมจาก Backup", "฿0.00", "#6366f1")
        self.backup_total_card.pack(side="left", fill="x", expand=True, padx=3)
        self.backup_count_card = self._create_stat_card(backup_stats, "📝 รายการจาก Backup", "0", "#8b5cf6")
        self.backup_count_card.pack(side="left", fill="x", expand=True, padx=3)
        self.backup_files_card = self._create_stat_card(backup_stats, "📁 จำนวนไฟล์", "0", "#a855f7")
        self.backup_files_card.pack(side="left", fill="x", expand=True, padx=3)
        
        # ตาราง backup
        self.backup_table = ctk.CTkScrollableFrame(tab, fg_color="#1a1a1a", corner_radius=10)
        self.backup_table.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        # ข้อความเริ่มต้น
        ctk.CTkLabel(
            self.backup_table,
            text="📂 กดปุ่ม 'ดึงข้อมูลจากไฟล์ Backup' เพื่อดูประวัติย้อนหลังจากไฟล์ .txt\nหรือเลือกไฟล์จาก dropdown ด้านบน",
            font=FONTS["body"],
            text_color="#888888"
        ).pack(pady=50)

    # =====================================================
    # TAB 3: สินค้าขายดี
    # =====================================================
    def setup_best_selling_tab(self):
        tab = self.tab_view.tab("สินค้าขายดี")
        
        ctrl_frame = ctk.CTkFrame(tab, fg_color="white", corner_radius=10)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(ctrl_frame, text="แสดงอันดับ TOP:", font=FONTS["body"]).pack(side="left", padx=15, pady=15)
        self.top_limit = ctk.CTkComboBox(ctrl_frame, values=["10", "20", "50", "100"], width=100)
        self.top_limit.set("20")
        self.top_limit.pack(side="left", padx=10)
        
        ctk.CTkButton(ctrl_frame, text="📊 วิเคราะห์อันดับ", command=self.load_best_selling).pack(side="left", padx=10)
        
        self.best_selling_container = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        self.best_selling_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # =====================================================
    # TAB 4: สินค้าใกล้หมด
    # =====================================================
    def setup_low_stock_tab(self):
        tab = self.tab_view.tab("สินค้าใกล้หมดสต็อก")
        
        info_frame = ctk.CTkFrame(tab, fg_color="white", corner_radius=10)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, 
            text="🔴 รายการสินค้าระดับวิกฤต (เหลือ <= 3 ชิ้น)", 
            font=FONTS["heading"],
            text_color=COLORS["danger"]
        ).pack(pady=15)
        
        self.low_stock_container = ctk.CTkScrollableFrame(tab, fg_color="white", corner_radius=10)
        self.low_stock_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # =====================================================
    # LOGIC — Helper
    # =====================================================
    def _create_stat_card(self, parent, title, value, color):
        """สร้างการ์ดสถิติ"""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10)
        ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color="white").pack(pady=(10, 3))
        value_label = ctk.CTkLabel(card, text=value, font=("Sarabun", 20, "bold"), text_color="white")
        value_label.pack(pady=(0, 10))
        card.value_label = value_label
        return card
    
    def _get_backup_files(self):
        """รวบรวมรายชื่อไฟล์ backup ทั้งหมด"""
        backup_dir = Path("Backup")
        files = ["-- ทั้งหมด --", "Current_Sales_Log.txt"]
        if backup_dir.exists():
            for f in sorted(backup_dir.glob("Sales_Summary_*.txt"), reverse=True):
                files.append(f.name)
        return files
    
    def _parse_backup_file(self, filepath):
        """
        แยกวิเคราะห์ไฟล์ backup .txt แล้วคืนค่า:
        (date_range_str, list_of_sales_dicts)
        
        แต่ละ sale dict มี: sale_number, time, total_amount, payment_method
        """
        sales = []
        date_range = ""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                # ดึงช่วงวันที่จาก header
                if line.startswith("ยอดขายวันที่"):
                    date_range = line.replace("ยอดขายวันที่", "").strip()
                    continue
                
                # ข้ามบรรทัด header/separator
                if not line or line.startswith("=") or line.startswith("-") or line.startswith("เลขที่"):
                    continue
                
                # Parse data row: "SL202602110001  | 15:50:31   |     111.00 | cash"
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    try:
                        sales.append({
                            'sale_number': parts[0],
                            'time': parts[1],
                            'total_amount': float(parts[2].replace(",", "")),
                            'payment_method': parts[3]
                        })
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            print(f"[ERROR] Parse backup file {filepath}: {e}")
        
        return date_range, sales
    
    def _extract_dates_from_range(self, date_range_str):
        """
        ดึงวันที่เริ่มต้นและสิ้นสุดจาก string เช่น "11/02/2026 - 11/02/2026"
        คืนค่า (start_date, end_date) เป็น datetime.date หรือ (None, None) ถ้า parse ไม่ได้
        """
        try:
            # Pattern: DD/MM/YYYY - DD/MM/YYYY
            match = re.findall(r'(\d{2}/\d{2}/\d{4})', date_range_str)
            if len(match) >= 2:
                start = datetime.strptime(match[0], "%d/%m/%Y").date()
                end = datetime.strptime(match[1], "%d/%m/%Y").date()
                return start, end
            elif len(match) == 1:
                d = datetime.strptime(match[0], "%d/%m/%Y").date()
                return d, d
        except:
            pass
        return None, None

    # =====================================================
    # LOGIC — Tab switching
    # =====================================================
    def on_tab_changed(self):
        tab = self.tab_view.get()
        if tab == "ยอดขายรวม":
            self.load_db_summary()
        elif tab == "ประวัติไฟล์ Backup":
            pass  # ให้ user กดปุ่มเอง
        elif tab == "สินค้าขายดี":
            self.load_best_selling()
        elif tab == "สินค้าใกล้หมดสต็อก":
            self.load_low_stock()

    # =====================================================
    # LOGIC — TAB 1: ยอดขายรวม (DB)
    # =====================================================
    def load_db_summary(self):
        """โหลดสรุปข้อมูลยอดขายจาก DB + Backup files รวมกัน"""
        for widget in self.db_summary_table.winfo_children(): 
            widget.destroy()
            
        try:
            filter_start = self.start_date.get_date()
            filter_end = self.end_date.get_date()
            start = filter_start.strftime("%Y-%m-%d")
            end = filter_end.strftime("%Y-%m-%d")
            
            all_rows = []  # รวมข้อมูลจากทุกแหล่ง
            
            # ===== แหล่งที่ 1: DB (ข้อมูลปัจจุบัน) =====
            self.db.connect()
            db_sales = self.db.fetch_all("""
                SELECT sale_number, sale_date, total_amount, payment_method, status 
                FROM sales 
                WHERE DATE(sale_date) BETWEEN ? AND ? 
                ORDER BY sale_date DESC
            """, (start, end))
            self.db.disconnect()
            
            for s in db_sales:
                # จัดการวันที่
                date_str = s['sale_date']
                try:
                    dt = datetime.strptime(s['sale_date'], DB_DATETIME_FORMAT)
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    try:
                        dt = datetime.strptime(s['sale_date'], DATETIME_FORMAT)
                        date_str = dt.strftime("%d/%m/%Y %H:%M")
                    except:
                        pass
                
                status_map = {
                    'completed': ('ปกติ', COLORS["success"]),
                    'returned': ('คืนแล้ว', COLORS["danger"]),
                    'voided': ('ยกเลิก', COLORS["danger"]),
                    'partially_returned': ('คืนบางส่วน', COLORS["warning"]),
                }
                status_text, status_color = status_map.get(s['status'], ('ปกติ', COLORS["success"]))
                
                all_rows.append({
                    'sale_number': s['sale_number'],
                    'date_str': date_str,
                    'total_amount': s['total_amount'],
                    'payment_method': s['payment_method'],
                    'status_text': status_text,
                    'status_color': status_color,
                    'source': '💾 DB',
                    'is_voided': s['status'] in ('returned', 'voided'),
                })
            
            # ===== แหล่งที่ 2: Backup .txt files =====
            backup_dir = Path("Backup")
            if backup_dir.exists():
                files_to_scan = []
                current = backup_dir / "Current_Sales_Log.txt"
                if current.exists():
                    files_to_scan.append(current)
                for f in sorted(backup_dir.glob("Sales_Summary_*.txt"), reverse=True):
                    files_to_scan.append(f)
                
                # เก็บ sale_number ที่มีใน DB แล้ว เพื่อไม่ให้ซ้ำ
                db_sale_numbers = set(s['sale_number'] for s in db_sales)
                
                for filepath in files_to_scan:
                    date_range, backup_sales = self._parse_backup_file(filepath)
                    if not backup_sales:
                        continue
                    
                    # ตรวจสอบว่าไฟล์นี้ตรงกับช่วงวันที่ที่เลือกไหม
                    file_start, file_end = self._extract_dates_from_range(date_range)
                    if file_start and file_end:
                        if file_end < filter_start or file_start > filter_end:
                            continue  # ไม่ overlap ข้าม
                    
                    for sale in backup_sales:
                        # ข้ามถ้าซ้ำกับ DB
                        if sale['sale_number'] in db_sale_numbers:
                            continue
                        
                        is_void = sale['sale_number'].startswith('VOID-')
                        
                        all_rows.append({
                            'sale_number': sale['sale_number'],
                            'date_str': f"{date_range} {sale['time']}",
                            'total_amount': sale['total_amount'],
                            'payment_method': sale['payment_method'],
                            'status_text': 'ยกเลิก' if is_void else 'สำรองแล้ว',
                            'status_color': COLORS["danger"] if is_void else '#6366f1',
                            'source': f"📄 {filepath.name[:25]}",
                            'is_voided': is_void,
                        })
            
            # ===== คำนวณสถิติรวม =====
            active_rows = [r for r in all_rows if not r['is_voided'] and r['total_amount'] > 0]
            total = sum(r['total_amount'] for r in active_rows)
            count = len(active_rows)
            avg = total / count if count > 0 else 0
            
            self.db_total_card.value_label.configure(text=f"฿{total:,.2f}")
            self.db_count_card.value_label.configure(text=f"{count:,}")
            self.db_avg_card.value_label.configure(text=f"฿{avg:,.2f}")
            
            if not all_rows:
                ctk.CTkLabel(
                    self.db_summary_table, 
                    text="ไม่พบข้อมูลยอดขายในช่วงเวลาที่เลือก\n(ยังไม่มีรายการขายหรือไฟล์ Backup ในช่วงนี้)", 
                    font=FONTS["body"],
                    text_color=COLORS["text_light"]
                ).pack(pady=30)
                return
    
            # Header
            h = ctk.CTkFrame(self.db_summary_table, fg_color=COLORS["primary"])
            h.pack(fill="x", pady=2)
            for t, w in [("เลขที่", 150), ("วันที่", 180), ("ยอดเงิน", 120), ("วิธีชำระ", 100), ("สถานะ", 100), ("แหล่งข้อมูล", 180)]:
                ctk.CTkLabel(h, text=t, width=w, text_color="white", font=FONTS["button"]).pack(side="left", padx=5, pady=8)
    
            # ข้อมูล
            for i, row in enumerate(all_rows):
                try:
                    bg = COLORS["light"] if i % 2 == 0 else "white"
                    if row['is_voided']:
                        bg = "#fff0f0"
                    r = ctk.CTkFrame(self.db_summary_table, fg_color=bg)
                    r.pack(fill="x", pady=1)
                    
                    text_color = "#999" if row['is_voided'] else COLORS["text_dark"]
                    
                    # แปลวิธีชำระเงินเป็นภาษาไทย
                    pm_map = {
                        'cash': 'เงินสด',
                        'transfer': 'โอนเงิน',
                        'qr': 'QR Code',
                        'mixed': 'จ่ายผสม',
                    }
                    pm_display = pm_map.get(str(row['payment_method']).lower(), row['payment_method'])
                    
                    ctk.CTkLabel(r, text=row['sale_number'], width=150, font=FONTS["body"], text_color=text_color).pack(side="left", padx=5, pady=6)
                    ctk.CTkLabel(r, text=row['date_str'], width=180, font=FONTS["body"], text_color=text_color).pack(side="left", padx=5)
                    ctk.CTkLabel(r, text=f"฿{row['total_amount']:,.2f}", width=120, font=("Sarabun", 14, "bold"), text_color=text_color).pack(side="left", padx=5)
                    ctk.CTkLabel(r, text=pm_display, width=100, font=FONTS["body"], text_color=text_color).pack(side="left", padx=5)
                    ctk.CTkLabel(r, text=row['status_text'], width=100, text_color=row['status_color'], font=FONTS["body"]).pack(side="left", padx=5)
                    ctk.CTkLabel(r, text=row['source'], width=180, font=FONTS["small"], text_color="#888").pack(side="left", padx=5)
                except Exception as e:
                    print(f"[ERROR] Error displaying sale row: {e}")
                    continue
        except Exception as e:
            print(f"[ERROR] load_db_summary error: {e}")
            ctk.CTkLabel(self.db_summary_table, text=f"เกิดข้อผิดพลาด: {e}", text_color=COLORS["danger"]).pack(pady=10)

    # =====================================================
    # LOGIC — TAB 2: ประวัติไฟล์ Backup
    # =====================================================
    def load_backup_by_date(self):
        """ดึงข้อมูลจากไฟล์ backup ทุกไฟล์ที่ตรงกับช่วงวันที่ที่เลือก"""
        for widget in self.backup_table.winfo_children():
            widget.destroy()
        
        filter_start = self.backup_start_date.get_date()
        filter_end = self.backup_end_date.get_date()
        
        backup_dir = Path("Backup")
        all_sales = []
        matched_files = 0
        
        # รวบรวมไฟล์ทั้งหมด
        files_to_scan = []
        if backup_dir.exists():
            # ไฟล์ปัจจุบัน
            current = backup_dir / "Current_Sales_Log.txt"
            if current.exists():
                files_to_scan.append(current)
            # ไฟล์ Summary เก่า
            for f in sorted(backup_dir.glob("Sales_Summary_*.txt"), reverse=True):
                files_to_scan.append(f)
        
        for filepath in files_to_scan:
            date_range, sales = self._parse_backup_file(filepath)
            
            if not sales:
                continue
            
            # ตรวจสอบว่าไฟล์นี้ตรงกับช่วงวันที่ที่เลือกไหม
            file_start, file_end = self._extract_dates_from_range(date_range)
            
            # ถ้า parse วันที่ได้ ให้ filter ตามช่วง
            if file_start and file_end:
                # ตรวจสอบว่ามี overlap กับช่วงที่เลือก
                if file_end < filter_start or file_start > filter_end:
                    continue  # ไม่ overlap ข้าม
            
            matched_files += 1
            for sale in sales:
                sale['source_file'] = filepath.name
                sale['date_range'] = date_range
                all_sales.append(sale)
        
        # อัพเดทสถิติ
        total = sum(s['total_amount'] for s in all_sales)
        self.backup_total_card.value_label.configure(text=f"฿{total:,.2f}")
        self.backup_count_card.value_label.configure(text=f"{len(all_sales):,}")
        self.backup_files_card.value_label.configure(text=f"{matched_files}")
        
        if not all_sales:
            ctk.CTkLabel(
                self.backup_table,
                text=f"📭 ไม่พบข้อมูลจากไฟล์ Backup ในช่วง {filter_start.strftime('%d/%m/%Y')} - {filter_end.strftime('%d/%m/%Y')}\n\n"
                     f"ไฟล์ backup จะถูกสร้างหลังจากกดปุ่ม 'ปิดยอดวัน' ในแท็บ 'ยอดขายรวม'",
                font=FONTS["body"],
                text_color="#888888"
            ).pack(pady=50)
            return
        
        self._render_backup_sales(all_sales)
    
    def load_single_backup_file(self):
        """โหลดไฟล์ backup เดี่ยวจาก dropdown"""
        selected = self.backup_file_var.get()
        
        if selected == "-- ทั้งหมด --":
            self.load_backup_by_date()
            return
        
        for widget in self.backup_table.winfo_children():
            widget.destroy()
        
        filepath = Path("Backup") / selected
        
        if not filepath.exists():
            ctk.CTkLabel(self.backup_table, text="📭 ไฟล์ไม่พบ", font=FONTS["body"], text_color="#888").pack(pady=50)
            return
        
        date_range, sales = self._parse_backup_file(filepath)
        
        if not sales:
            ctk.CTkLabel(
                self.backup_table,
                text=f"📭 ไฟล์ {selected} ยังไม่มีรายการขาย",
                font=FONTS["body"],
                text_color="#888888"
            ).pack(pady=50)
            
            # อัพเดทสถิติ
            self.backup_total_card.value_label.configure(text="฿0.00")
            self.backup_count_card.value_label.configure(text="0")
            self.backup_files_card.value_label.configure(text="1")
            return
        
        for s in sales:
            s['source_file'] = selected
            s['date_range'] = date_range
        
        total = sum(s['total_amount'] for s in sales)
        self.backup_total_card.value_label.configure(text=f"฿{total:,.2f}")
        self.backup_count_card.value_label.configure(text=f"{len(sales):,}")
        self.backup_files_card.value_label.configure(text="1")
        
        self._render_backup_sales(sales)
    
    def _render_backup_sales(self, sales):
        """แสดงรายการขายจาก backup ในตาราง"""
        # Header
        h = ctk.CTkFrame(self.backup_table, fg_color="#6366f1")
        h.pack(fill="x", pady=2)
        for t, w in [("เลขที่", 160), ("เวลา", 100), ("ยอดเงิน", 120), ("วิธีชำระ", 100), ("ช่วงวันที่", 200), ("ไฟล์", 250)]:
            ctk.CTkLabel(h, text=t, width=w, text_color="white", font=FONTS["button"]).pack(side="left", padx=5, pady=8)
        
        # ข้อมูล
        current_file = None
        for i, sale in enumerate(sales):
            # แสดงชื่อไฟล์เป็น group header ถ้าเปลี่ยนไฟล์
            if sale['source_file'] != current_file:
                current_file = sale['source_file']
                file_header = ctk.CTkFrame(self.backup_table, fg_color="#2d2d3d")
                file_header.pack(fill="x", pady=(8, 2))
                ctk.CTkLabel(
                    file_header,
                    text=f"📄 {current_file}  —  {sale.get('date_range', '')}",
                    font=("Courier New", 12, "bold"),
                    text_color="#a78bfa"
                ).pack(side="left", padx=10, pady=5)
            
            bg = "#1e1e2e" if i % 2 == 0 else "#252535"
            r = ctk.CTkFrame(self.backup_table, fg_color=bg)
            r.pack(fill="x", pady=1)
            
            # แปลวิธีชำระเงินเป็นภาษาไทย
            pm_map = {
                'cash': 'เงินสด',
                'transfer': 'โอนเงิน',
                'qr': 'QR Code',
                'mixed': 'จ่ายผสม',
            }
            pm_display = pm_map.get(str(sale['payment_method']).lower(), sale['payment_method'])
            
            ctk.CTkLabel(r, text=sale['sale_number'], width=160, font=("Courier New", 13), text_color="#e2e8f0").pack(side="left", padx=5, pady=5)
            ctk.CTkLabel(r, text=sale['time'], width=100, font=("Courier New", 13), text_color="#94a3b8").pack(side="left", padx=5)
            ctk.CTkLabel(r, text=f"฿{sale['total_amount']:,.2f}", width=120, font=("Courier New", 13, "bold"), text_color="#4ade80").pack(side="left", padx=5)
            ctk.CTkLabel(r, text=pm_display, width=100, font=("Courier New", 13), text_color="#94a3b8").pack(side="left", padx=5)
            ctk.CTkLabel(r, text=sale.get('date_range', ''), width=200, font=("Courier New", 11), text_color="#64748b").pack(side="left", padx=5)
            ctk.CTkLabel(r, text=sale['source_file'], width=250, font=("Courier New", 10), text_color="#475569").pack(side="left", padx=5)

    # =====================================================
    # LOGIC — ปิดยอดวัน
    # =====================================================
    def clear_daily_list(self):
        if messagebox.askyesno("ยืนยันการปิดยอด", 
            "ต้องการปิดยอดรายวันและเริ่มใหม่หรือไม่?\n\n"
            "ระบบจะทำสิ่งเหล่านี้:\n"
            "1. 💾 สำรองข้อมูลเป็นไฟล์ Excel (.xlsx)\n"
            "2. 📄 สำรองข้อมูลเป็นไฟล์ Text (.txt)\n"
            "3. 🧹 ล้างข้อมูลในฐานข้อมูล\n\n"
            "ข้อมูลจะยังคงเรียกดูได้จากแท็บ 'ประวัติไฟล์ Backup'"
        ):
            backup_results = []
            today = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. Auto-Export Excel ก่อนเคลียร์ DB
            try:
                self.db.connect()
                sales = self.db.fetch_all("""
                    SELECT s.sale_id, s.sale_number, s.sale_date,
                           s.subtotal, s.discount_amount, s.tax_amount, 
                           s.total_amount, s.paid_amount, s.change_amount, 
                           s.payment_method, s.status,
                           u.full_name as cashier_name,
                           GROUP_CONCAT(si.product_name || ' x' || si.quantity) as items
                    FROM sales s
                    LEFT JOIN users u ON s.user_id = u.user_id
                    LEFT JOIN sale_items si ON s.sale_id = si.sale_id
                    GROUP BY s.sale_id
                    ORDER BY s.sale_id DESC
                """)
                self.db.disconnect()
                
                if sales:
                    excel_path = Path("Backup") / f"ยอดขาย_ปิดร้าน_{today}.xlsx"
                    
                    columns = [
                        "เลขที่", "วันที่/เวลา", "ยอดรวม", "ส่วนลด", "ภาษี", 
                        "ยอดสุทธิ", "รับเงิน", "เงินทอน", "วิธีชำระ", "สถานะ",
                        "พนักงาน", "รายการสินค้า"
                    ]
                    
                    export_data = []
                    for sale in sales:
                        export_data.append({
                            "เลขที่": sale['sale_number'],
                            "วันที่/เวลา": sale['sale_date'],
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
                    
                    if ExcelManager.export_to_excel(export_data, columns, str(excel_path), sheet_name="ยอดขาย", title=f"รายงานปิดยอดขายประจำวัน ({today})"):
                        backup_results.append(f"📊 Excel: {excel_path.name}")
                    else:
                        backup_results.append("📊 Excel: ❌ ล้มเหลว")
                else:
                    backup_results.append("📊 Excel: ไม่มีข้อมูลให้ export")
                    
            except Exception as e:
                backup_results.append(f"📊 Excel: ❌ ล้มเหลว ({e})")
                print(f"[ERROR] Auto Excel export failed: {e}")
            
            # 2. หมุนไฟล์ Log (Backup เป็น .txt)
            try:
                f = self.slm.clear_and_rotate()
                backup_results.append(f"📄 TXT: {Path(f).name if f else 'บันทึกแล้ว'}")
            except Exception as e:
                backup_results.append(f"📄 TXT: ❌ ล้มเหลว ({e})")
            
            # 3. ปิดยอดในฐานข้อมูล (ปรับเป็น Archived แทนการลบข้อมูลจริง)
            try:
                self.db.connect()
                self.db.execute("UPDATE sales SET is_archived = 1 WHERE is_archived = 0")
                self.db.execute("UPDATE returns SET is_archived = 1 WHERE is_archived = 0")
                self.db.disconnect()
                
                results_text = "\n".join(backup_results)
                messagebox.showinfo(
                    "ปิดยอดสำเร็จ",
                    f"ปิดยอดรายวันและบันทึกประวัติเรียบร้อย\n\n"
                    f"📁 ไฟล์สำรองที่สร้าง:\n{results_text}\n\n"
                    f"📂 เก็บอยู่ในโฟลเดอร์ Backup/\n"
                    f"ข้อมูลเดิมยังอยู่ในฐานข้อมูลและไฟล์สำรองทั้งหมด"
                )
                
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถอัปเดตสถานะปิดยอดในฐานข้อมูลได้: {e}")
            
            # 4. อัพเดท dropdown
            self.backup_file_combo.configure(values=self._get_backup_files())
            
            # 5. อัพเดท UI
            self.load_db_summary()

    # =====================================================
    # LOGIC — Export Excel (ใช้ ExcelManager 100%)
    # =====================================================
    def export_to_excel(self):
        """Export ข้อมูลยอดขายเป็น Excel"""
        start = self.start_date.get_date().strftime("%Y-%m-%d")
        end = self.end_date.get_date().strftime("%Y-%m-%d")
        
        self.db.connect()
        sales = self.db.fetch_all("""
            SELECT s.sale_id, s.sale_number, s.sale_date,
                   s.subtotal, s.discount_amount, s.tax_amount, 
                   s.total_amount, s.paid_amount, s.change_amount, 
                   s.payment_method, s.status,
                   u.full_name as cashier_name,
                   GROUP_CONCAT(si.product_name || ' x' || si.quantity) as items
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE DATE(s.sale_date) BETWEEN ? AND ?
            GROUP BY s.sale_id
            ORDER BY s.sale_id DESC
        """, (start, end))
        self.db.disconnect()
        
        if not sales:
            messagebox.showwarning("แจ้งเตือน", "ไม่มีข้อมูลให้ Export\n(ลองดูข้อมูลจากแท็บ 'ประวัติไฟล์ Backup' แทน)")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=f"ยอดขาย_{start}_ถึง_{end}.xlsx"
        )
        
        if not filename:
            return
        
        columns = [
            "เลขที่", "วันที่/เวลา", "ยอดรวม", "ส่วนลด", "ภาษี", 
            "ยอดสุทธิ", "รับเงิน", "เงินทอน", "วิธีชำระ", "สถานะ",
            "พนักงาน", "รายการสินค้า"
        ]
        
        export_data = []
        for sale in sales:
            export_data.append({
                "เลขที่": sale['sale_number'],
                "วันที่/เวลา": sale['sale_date'],
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
            sheet_name="ยอดขาย",
            title=f"รายงานสรุปยอดขาย ({start} ถึง {end})"
        )
        
        if success:
            messagebox.showinfo("สำเร็จ", f"Export สำเร็จ 100%!\nบันทึกที่: {filename}")
        else:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถบันทึกไฟล์ Excel ได้")

    # =====================================================
    # LOGIC — TAB 3: สินค้าขายดี
    # =====================================================
    def load_best_selling(self):
        for widget in self.best_selling_container.winfo_children(): widget.destroy()
        limit = int(self.top_limit.get())
        
        self.db.connect()
        items = self.db.fetch_all(f"""
            SELECT product_name, SUM(quantity) as qty, SUM(total_price) as total
            FROM sale_items
            GROUP BY product_id
            ORDER BY qty DESC
            LIMIT {limit}
        """)
        self.db.disconnect()

        if not items:
            ctk.CTkLabel(self.best_selling_container, text="ยังไม่มีข้อมูลการขายสำหรับวิเคราะห์").pack(pady=20)
            return

        h = ctk.CTkFrame(self.best_selling_container, fg_color=COLORS["secondary"])
        h.pack(fill="x", pady=5)
        for t, w in [("สินค้า", 300), ("จำนวนที่ขายได้", 150), ("รวมยอดขาย", 150)]:
            ctk.CTkLabel(h, text=t, width=w, text_color="white", font=FONTS["button"]).pack(side="left", padx=10, pady=10)

        for i, item in enumerate(items):
            bg = "#f9f9f9" if i%2==0 else "white"
            r = ctk.CTkFrame(self.best_selling_container, fg_color=bg)
            r.pack(fill="x", pady=1)
            ctk.CTkLabel(r, text=item['product_name'], width=300, anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(r, text=f"{item['qty']:,}", width=150, font=("Sarabun", 14, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(r, text=f"฿{item['total']:,.2f}", width=150, text_color=COLORS["primary"]).pack(side="left", padx=10)

    # =====================================================
    # LOGIC — TAB 4: สินค้าใกล้หมด
    # =====================================================
    def load_low_stock(self):
        for widget in self.low_stock_container.winfo_children(): widget.destroy()
        
        self.db.connect()
        items = self.db.fetch_all("SELECT product_name, barcode, stock_quantity, min_stock FROM products WHERE stock_quantity <= 3 AND is_active = 1 ORDER BY stock_quantity ASC")
        self.db.disconnect()

        if not items:
            ctk.CTkLabel(self.low_stock_container, text="ขณะนี้ไม่มีสินค้าที่อยู่ในระดับวิกฤต", text_color=COLORS["success"]).pack(pady=30)
            return

        for item in items:
            qty = item['stock_quantity']
            color = COLORS["danger"] if qty <= 3 else COLORS["warning"]
            icon = "🔴" if qty <= 3 else "🟡"
            
            card = ctk.CTkFrame(self.low_stock_container, fg_color="white", border_width=2, border_color=color)
            card.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(card, text=f"{icon} {item['product_name']}", font=FONTS["heading"], text_color=color, anchor="w").pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(card, text=f"บาร์โค้ด: {item['barcode']}", font=FONTS["body"]).pack(side="left", padx=20)
            
            qty_frame = ctk.CTkFrame(card, fg_color=color, corner_radius=10)
            qty_frame.pack(side="right", padx=20)
            ctk.CTkLabel(qty_frame, text=f"เหลือ {qty} ชิ้น", font=("Sarabun", 16, "bold"), text_color="white").pack(padx=15, pady=5)
