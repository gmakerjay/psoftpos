# -*- coding: utf-8 -*-
"""
หน้าจัดการสมาชิก (Member Management)
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
from datetime import datetime

class MemberManagementFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการสมาชิกแบบครบวงจร"""
    
    def __init__(self, parent, user_id):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.db = DatabaseManager()
        
        self.create_widgets()
        self.load_members()
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header_frame,
            text="👥 ระบบจัดการสมาชิก (Member Management)",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        ).pack(side="left")
        
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(
            btn_frame,
            text="⚙️ ตั้งค่าระดับสมาชิก (Tiers)",
            font=FONTS["button"],
            fg_color=COLORS["secondary"],
            command=self.show_tiers_dialog
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="➕ เพิ่มสมาชิก",
            font=FONTS["button"],
            fg_color=COLORS["success"],
            command=self.show_add_member_dialog
        ).pack(side="left", padx=5)
        
        # Search & Filter
        search_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        search_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍 ค้นหาสมาชิก:",
            font=FONTS["body"]
        ).pack(side="left", padx=20, pady=15)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="พิมพ์ ชื่อ / เบอร์โทร / Username...",
            font=FONTS["body"],
            width=300,
            height=35
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.load_members())
        
        ctk.CTkButton(
            search_frame,
            text="ค้นหา",
            font=FONTS["button"],
            width=100,
            height=40,
            fg_color=COLORS["primary"],
            command=self.load_members
        ).pack(side="left", padx=10)
        
        # Member Table Frame
        self.table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Table Header
        h_row = ctk.CTkFrame(self.table_frame, fg_color=COLORS["primary"], height=40)
        h_row.pack(fill="x")
        h_row.pack_propagate(False)
        
        headers = [
            ("ID", 50),
            ("ชื่อสมาชิก", 150),
            ("เบอร์โทร", 120),
            ("ที่อยู่", 180),
            ("สิทธิพิเศษ", 180),
            ("แต้มสะสม", 100),
            ("จัดการ", 150)
        ]
        
        for text, w in headers:
            ctk.CTkLabel(
                h_row,
                text=text,
                font=FONTS["button"],
                text_color="white",
                width=w
            ).pack(side="left", padx=3, pady=8)
            
        # Scrollable container for members rows
        self.list_frame = ctk.CTkScrollableFrame(self.table_frame, fg_color="white")
        self.list_frame.pack(fill="both", expand=True)
        
    def load_members(self):
        """โหลดข้อมูลสมาชิก"""
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        query = """
            SELECT m.*, t.tier_name, t.discount_percent as tier_discount
            FROM members m
            LEFT JOIN member_tiers t ON m.tier_id = t.tier_id
        """
        params = []
        
        search_val = self.search_entry.get().strip()
        if search_val:
            query += " WHERE m.name LIKE ? OR m.phone LIKE ? OR m.address LIKE ? OR m.privilege LIKE ?"
            params = [f"%{search_val}%", f"%{search_val}%", f"%{search_val}%", f"%{search_val}%"]
            
        query += " ORDER BY m.member_id DESC"
        
        self.db.connect()
        members = self.db.fetch_all(query, tuple(params))
        self.db.disconnect()
        
        if not members:
            ctk.CTkLabel(
                self.list_frame,
                text="ไม่พบข้อมูลสมาชิก",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            ).pack(pady=30)
            return
            
        for i, member in enumerate(members):
            bg = COLORS["light"] if i % 2 == 0 else "white"
            row = ctk.CTkFrame(self.list_frame, fg_color=bg, height=50)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            
            # ID
            ctk.CTkLabel(row, text=str(member['member_id']), font=FONTS["body"], width=50).pack(side="left", padx=3)
            # Name
            ctk.CTkLabel(row, text=member['name'], font=FONTS["body"], width=150, anchor="w").pack(side="left", padx=3)
            # Phone
            ctk.CTkLabel(row, text=member['phone'] or '-', font=FONTS["body"], width=120).pack(side="left", padx=3)
            # Address
            ctk.CTkLabel(row, text=member['address'] or '-', font=FONTS["body"], width=180, anchor="w").pack(side="left", padx=3)
            # Privilege
            ctk.CTkLabel(row, text=member['privilege'] or '-', font=FONTS["body"], width=180, anchor="w").pack(side="left", padx=3)
            # Points
            ctk.CTkLabel(row, text=f"{member['points'] or 0} แต้ม", font=("Sarabun", 13, "bold"), text_color=COLORS["success"], width=100).pack(side="left", padx=3)
            
            # Action Buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=150)
            btn_frame.pack(side="left", padx=3)
            btn_frame.pack_propagate(False)
            
            ctk.CTkButton(btn_frame, text="👁️", font=("Arial", 14), width=40, height=30, fg_color=COLORS["info"], command=lambda m=member: self.view_member_history(m)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="✏️", font=("Arial", 14), width=40, height=30, fg_color=COLORS["warning"], command=lambda m=member: self.show_edit_member_dialog(m)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="🗑️", font=("Arial", 14), width=40, height=30, fg_color=COLORS["danger"], command=lambda m_id=member['member_id']: self.delete_member(m_id)).pack(side="left", padx=2)

    def show_add_member_dialog(self):
        self.show_member_dialog("เพิ่มสมาชิก")

    def show_edit_member_dialog(self, member):
        self.show_member_dialog("แก้ไขสมาชิก", member)

    def show_member_dialog(self, title, member=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("600x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Scrollable Form
        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(scroll, text=title, font=FONTS["heading"], text_color=COLORS["primary"]).pack(pady=(0, 20))
        
        ctk.CTkLabel(scroll, text="ชื่อ-นามสกุลสมาชิก:", font=FONTS["body"]).pack(anchor="w")
        name_entry = ctk.CTkEntry(scroll, width=500, height=35)
        name_entry.pack(pady=5)
        if member: name_entry.insert(0, member['name'] or '')
        
        ctk.CTkLabel(scroll, text="เบอร์โทรศัพท์:", font=FONTS["body"]).pack(anchor="w")
        phone_entry = ctk.CTkEntry(scroll, width=500, height=35)
        phone_entry.pack(pady=5)
        if member: phone_entry.insert(0, member['phone'] or '')
        
        ctk.CTkLabel(scroll, text="ที่อยู่:", font=FONTS["body"]).pack(anchor="w")
        address_entry = ctk.CTkEntry(scroll, width=500, height=35)
        address_entry.pack(pady=5)
        if member: address_entry.insert(0, member['address'] or '')
        
        ctk.CTkLabel(scroll, text="สิทธิพิเศษ / รายละเอียดเพิ่มเติม:", font=FONTS["body"]).pack(anchor="w")
        privilege_entry = ctk.CTkEntry(scroll, width=500, height=35)
        privilege_entry.pack(pady=5)
        if member: privilege_entry.insert(0, member['privilege'] or '')
        
        ctk.CTkLabel(scroll, text="แต้มสะสมปัจจุบัน:", font=FONTS["body"]).pack(anchor="w")
        points_entry = ctk.CTkEntry(scroll, width=500, height=35)
        points_entry.pack(pady=5)
        points_entry.insert(0, str(member['points'] if member else 0))
        
        def save():
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            address = address_entry.get().strip()
            privilege = privilege_entry.get().strip()
            
            try:
                points = int(points_entry.get().strip())
            except ValueError:
                messagebox.showerror("ผิดพลาด", "กรุณากรอกแต้มสะสมให้เป็นตัวเลขจำนวนเต็ม")
                return
                
            if not name:
                messagebox.showerror("ผิดพลาด", "กรุณากรอกชื่อ-นามสกุลสมาชิก")
                return
                
            data = {
                'name': name,
                'phone': phone,
                'address': address,
                'privilege': privilege,
                'points': points
            }
            
            self.db.connect()
            if member:
                query = "UPDATE members SET " + ", ".join([f"{k} = ?" for k in data.keys()]) + " WHERE member_id = ?"
                params = list(data.values()) + [member['member_id']]
                success = self.db.execute(query, params)
            else:
                # ตั้งค่าเริ่มต้นอื่นๆ ให้เข้ากันได้กับระดับสมาชิกทั่วไป (General Tier)
                gen_tier = self.db.fetch_one("SELECT tier_id FROM member_tiers WHERE tier_name LIKE '%General%'")
                tier_id = gen_tier['tier_id'] if gen_tier else 1
                
                data['tier_id'] = tier_id
                data['status'] = 'active'
                
                query = "INSERT INTO members (" + ", ".join(data.keys()) + ") VALUES (" + ", ".join(["?" for _ in data]) + ")"
                success = self.db.execute(query, list(data.values()))
            self.db.disconnect()
            
            if success:
                messagebox.showinfo("สำเร็จ", "บันทึกข้อมูลสมาชิกเรียบร้อย")
                dialog.destroy()
                self.load_members()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถบันทึกข้อมูลได้")
                
        ctk.CTkButton(scroll, text="💾 บันทึกข้อมูล", font=("Sarabun", 16, "bold"), fg_color=COLORS["success"], height=45, command=save).pack(pady=30)

    def show_credit_adjust_dialog(self, member):
        """แสดง dialog ปรับปรุงคะแนน/แต้ม/กระเป๋าเงิน (เตรียมสำหรับ POS Wallet/Points)"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"สะสมแต้ม & Credit - {member['name']}")
        dialog.geometry("450x450")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"💰 แต้ม & กระเป๋าเงิน\nคุณ {member['name']}", font=FONTS["heading"], text_color=COLORS["primary"]).pack(pady=20)
        
        info_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        points_label = ctk.CTkLabel(info_frame, text=f"แต้มสะสมปัจจุบัน: {member['points'] or 0} แต้ม", font=FONTS["body"])
        points_label.pack(pady=5)
        
        wallet_label = ctk.CTkLabel(info_frame, text=f"ยอดเงินใน Wallet: ฿{member['wallet_balance'] or 0.0:.2f}", font=FONTS["body"])
        wallet_label.pack(pady=5)
        
        credit_label = ctk.CTkLabel(info_frame, text=f"วงเงินเครดิตคงเหลือ: ฿{member['credit_balance'] or 0.0:.2f}", font=FONTS["body"])
        credit_label.pack(pady=5)
        
        # ช่องปรับแต้ม
        ctk.CTkLabel(dialog, text="ปรับแต้มสะสม (+/-):", font=FONTS["small"]).pack(padx=30, anchor="w", pady=(15, 0))
        pts_entry = ctk.CTkEntry(dialog, placeholder_text="กรอกแต้ม เช่น +50 หรือ -10", width=380)
        pts_entry.pack(padx=30, pady=5)
        pts_entry.insert(0, "0")
        
        # ช่องปรับยอดเงิน Wallet
        ctk.CTkLabel(dialog, text="ปรับเงินในกระเป๋า (Wallet) (+/-):", font=FONTS["small"]).pack(padx=30, anchor="w", pady=(10, 0))
        wallet_entry = ctk.CTkEntry(dialog, placeholder_text="กรอกจำนวนเงิน เช่น +100.0 หรือ -50.0", width=380)
        wallet_entry.pack(padx=30, pady=5)
        wallet_entry.insert(0, "0.0")
        
        def save_adjust():
            try:
                pts_adj = int(pts_entry.get().strip())
                wallet_adj = float(wallet_entry.get().strip())
            except ValueError:
                messagebox.showerror("ผิดพลาด", "กรุณากรอกแต้มและยอดเงินให้ถูกต้อง")
                return
                
            new_pts = max(0, (member['points'] or 0) + pts_adj)
            new_wallet = max(0.0, (member['wallet_balance'] or 0.0) + wallet_adj)
            
            self.db.connect()
            success = self.db.execute("""
                UPDATE members 
                SET points = ?, wallet_balance = ?
                WHERE member_id = ?
            """, (new_pts, new_wallet, member['member_id']))
            self.db.disconnect()
            
            if success:
                messagebox.showinfo("สำเร็จ", "ปรับปรุงยอดเงินสะสมเรียบร้อย")
                dialog.destroy()
                self.load_members()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถปรับปรุงข้อมูลได้")
                
        ctk.CTkButton(dialog, text="ยืนยันการปรับปรุง", fg_color=COLORS["success"], height=40, command=save_adjust).pack(pady=25)

    def delete_member(self, member_id):
        if messagebox.askyesno("ยืนยันการลบ", "คุณแน่ใจว่าต้องการลบสมาชิกรายนี้ใช่หรือไม่?\n⚠️ ประวัติการซื้อขายที่ผูกกับสมาชิกจะไม่ถูกลบ แต่รหัสสมาชิกจะหลุดออก"):
            self.db.connect()
            # ตัด member_id ใน sales เป็น NULL ก่อนลบ เพื่อรักษา compatibility
            self.db.execute("UPDATE sales SET member_id = NULL WHERE member_id = ?", (member_id,))
            success = self.db.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
            self.db.disconnect()
            
            if success:
                self.load_members()
            else:
                messagebox.showerror("ผิดพลาด", "ไม่สามารถลบข้อมูลสมาชิกได้")

    def show_tiers_dialog(self):
        """ตั้งค่าระดับสมาชิก (Tiers)"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("ตั้งค่าระดับสมาชิก")
        dialog.geometry("600x550")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="⚙️ ตั้งค่าระดับสมาชิก (Member Tiers)", font=FONTS["heading"], text_color=COLORS["primary"]).pack(pady=20)
        
        tiers_frame = ctk.CTkScrollableFrame(dialog, fg_color="white", corner_radius=10, height=300)
        tiers_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        def load_tiers():
            for widget in tiers_frame.winfo_children():
                widget.destroy()
                
            self.db.connect()
            tiers = self.db.fetch_all("SELECT * FROM member_tiers ORDER BY min_points")
            self.db.disconnect()
            
            # Header
            hr = ctk.CTkFrame(tiers_frame, fg_color=COLORS["primary"])
            hr.pack(fill="x", pady=2)
            ctk.CTkLabel(hr, text="ระดับสมาชิก", font=FONTS["button"], text_color="white", width=120).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(hr, text="ส่วนลด (%)", font=FONTS["button"], text_color="white", width=100).pack(side="left", padx=10)
            ctk.CTkLabel(hr, text="แต้มขั้นต่ำ", font=FONTS["button"], text_color="white", width=100).pack(side="left", padx=10)
            ctk.CTkLabel(hr, text="จัดการ", font=FONTS["button"], text_color="white", width=120).pack(side="left", padx=10)
            
            for tier in tiers:
                tr = ctk.CTkFrame(tiers_frame, fg_color=COLORS["light"])
                tr.pack(fill="x", pady=1)
                
                ctk.CTkLabel(tr, text=tier['tier_name'], font=("Sarabun", 13, "bold"), width=120).pack(side="left", padx=10, pady=5)
                ctk.CTkLabel(tr, text=f"{tier['discount_percent']}%", font=FONTS["body"], width=100).pack(side="left", padx=10)
                ctk.CTkLabel(tr, text=str(tier['min_points']), font=FONTS["body"], width=100).pack(side="left", padx=10)
                
                tb_frame = ctk.CTkFrame(tr, fg_color="transparent")
                tb_frame.pack(side="left", padx=10)
                
                # ลบระดับสมาชิกที่ไม่ใช่ General (General เป็น default ห้ามลบ)
                if tier['tier_name'] != "General":
                    ctk.CTkButton(tb_frame, text="ลบ", width=50, height=25, fg_color=COLORS["danger"], command=lambda t_id=tier['tier_id']: delete_tier(t_id)).pack(side="left", padx=2)
                else:
                    ctk.CTkLabel(tb_frame, text="ระดับเริ่มต้น", font=FONTS["small"], text_color=COLORS["text_light"], width=50).pack(side="left", padx=2)
                    
        def add_tier():
            add_win = ctk.CTkToplevel(dialog)
            add_win.title("เพิ่มระดับสมาชิกใหม่")
            add_win.geometry("400x300")
            add_win.transient(dialog)
            add_win.grab_set()
            
            ctk.CTkLabel(add_win, text="เพิ่มระดับใหม่", font=FONTS["heading"]).pack(pady=15)
            
            ctk.CTkLabel(add_win, text="ชื่อระดับ (เช่น Silver, Gold, Platinum):", font=FONTS["body"]).pack(padx=20, anchor="w")
            t_name_entry = ctk.CTkEntry(add_win, width=350)
            t_name_entry.pack(padx=20, pady=5)
            
            ctk.CTkLabel(add_win, text="ส่วนลดส่วนตัว (%):", font=FONTS["body"]).pack(padx=20, anchor="w")
            t_disc_entry = ctk.CTkEntry(add_win, width=350)
            t_disc_entry.pack(padx=20, pady=5)
            t_disc_entry.insert(0, "0")
            
            ctk.CTkLabel(add_win, text="แต้มสะสมขั้นต่ำที่จะได้ระดับนี้:", font=FONTS["body"]).pack(padx=20, anchor="w")
            t_pts_entry = ctk.CTkEntry(add_win, width=350)
            t_pts_entry.pack(padx=20, pady=5)
            t_pts_entry.insert(0, "0")
            
            def save_new_tier():
                t_name = t_name_entry.get().strip()
                try:
                    t_disc = float(t_disc_entry.get().strip())
                    t_pts = int(t_pts_entry.get().strip())
                except ValueError:
                    messagebox.showerror("ผิดพลาด", "กรุณากรอกตัวเลขส่วนลดและแต้มให้ถูกต้อง")
                    return
                    
                if not t_name:
                    messagebox.showerror("ผิดพลาด", "กรุณากรอกชื่อระดับสมาชิก")
                    return
                    
                self.db.connect()
                success = self.db.execute("""
                    INSERT INTO member_tiers (tier_name, discount_percent, min_points)
                    VALUES (?, ?, ?)
                """, (t_name, t_disc, t_pts))
                self.db.disconnect()
                
                if success:
                    messagebox.showinfo("สำเร็จ", "เพิ่มระดับสมาชิกสำเร็จ")
                    add_win.destroy()
                    load_tiers()
                else:
                    messagebox.showerror("ผิดพลาด", "ไม่สามารถเพิ่มข้อมูลได้ (ชื่ออาจซ้ำ)")
                    
            ctk.CTkButton(add_win, text="บันทึกระดับ", fg_color=COLORS["success"], height=35, command=save_new_tier).pack(pady=20)
            
        def delete_tier(tier_id):
            if messagebox.askyesno("ยืนยันการลบ", "คุณต้องการลบระดับสมาชิกนี้ใช่หรือไม่?\n⚠️ สมาชิกที่มีระดับนี้อยู่จะถูกลดระดับลงมาเป็น General อัตโนมัติ"):
                self.db.connect()
                # ค้นหารหัส General
                gen_tier = self.db.fetch_one("SELECT tier_id FROM member_tiers WHERE tier_name = 'General'")
                gen_id = gen_tier['tier_id'] if gen_tier else 1
                # ลดสิทธิ์สมาชิก
                self.db.execute("UPDATE members SET tier_id = ? WHERE tier_id = ?", (gen_id, tier_id))
                # ลบ
                success = self.db.execute("DELETE FROM member_tiers WHERE tier_id = ?", (tier_id,))
                self.db.disconnect()
                if success:
                    load_tiers()
                    self.load_members()
                else:
                    messagebox.showerror("ผิดพลาด", "ไม่สามารถลบข้อมูลระดับสมาชิกได้")
                    
        load_tiers()
        ctk.CTkButton(dialog, text="➕ เพิ่มระดับสมาชิกใหม่", fg_color=COLORS["success"], height=40, command=add_tier).pack(pady=15)

    def view_member_history(self, member):
        """ดูประวัติการทำธุรกรรมย้อนหลังของสมาชิกรายคน (Member History)"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"ประวัติธุรกรรม - {member['name']}")
        dialog.geometry("850x650")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text=f"📋 ประวัติการซื้อสินค้าของสมาชิก\nคุณ {member['name']}", font=FONTS["heading"], text_color=COLORS["primary"]).pack(pady=20)
        
        # ตารางประวัติ
        history_frame = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
        history_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        h_row = ctk.CTkFrame(history_frame, fg_color=COLORS["secondary"], height=40)
        h_row.pack(fill="x")
        h_row.pack_propagate(False)
        
        headers = [
            ("เลขบิล", 100),
            ("วันที่/เวลา", 120),
            ("จำนวนชิ้น", 60),
            ("ยอดสุทธิ", 80),
            ("แต้ม (ได้/ใช้)", 100),
            ("วิธีชำระ", 70),
            ("พนักงานขาย", 100),
            ("รายการสินค้าที่ซื้อ", 180)
        ]
        
        for text, w in headers:
            ctk.CTkLabel(h_row, text=text, font=FONTS["button"], text_color="white", width=w).pack(side="left", padx=2, pady=8)
            
        list_scroll = ctk.CTkScrollableFrame(history_frame, fg_color="white")
        list_scroll.pack(fill="both", expand=True)
        
        # ดึงประวัติจาก sales ที่ผูกกับ member_id รายนี้
        self.db.connect()
        sales = self.db.fetch_all("""
            SELECT s.*, u.full_name as cashier_name,
                   COUNT(si.item_id) as item_count,
                   GROUP_CONCAT(COALESCE(si.product_name, 'Unknown') || ' x' || COALESCE(si.quantity, 0), ', ') as items_list
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.user_id
            LEFT JOIN sale_items si ON s.sale_id = si.sale_id
            WHERE s.member_id = ?
            GROUP BY s.sale_id
            ORDER BY s.sale_date DESC
        """, (member['member_id'],))
        self.db.disconnect()
        
        if not sales:
            ctk.CTkLabel(list_scroll, text="ยังไม่มีประวัติการซื้อสินค้าของสมาชิกรายนี้", font=FONTS["body"], text_color=COLORS["text_light"]).pack(pady=40)
        else:
            for i, sale in enumerate(sales):
                bg = COLORS["light"] if i % 2 == 0 else "white"
                row = ctk.CTkFrame(list_scroll, fg_color=bg, height=50)
                row.pack(fill="x", pady=1)
                row.pack_propagate(False)
                
                # Date format
                time_str = sale['sale_date']
                try:
                    dt = datetime.strptime(sale['sale_date'], DB_DATETIME_FORMAT)
                    time_str = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    pass
                    
                pts_earned = sale['points_earned'] if 'points_earned' in sale.keys() else 0
                pts_used = sale['points_used'] if 'points_used' in sale.keys() else 0
                if pts_earned is None: pts_earned = 0
                if pts_used is None: pts_used = 0
                pts_display = f"+{pts_earned} / -{pts_used}"
                
                ctk.CTkLabel(row, text=sale['sale_number'], font=FONTS["body"], width=100).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=time_str, font=FONTS["body"], width=120).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=str(sale['item_count']), font=FONTS["body"], width=60).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=f"฿{sale['total_amount']:,.2f}", font=("Sarabun", 12, "bold"), text_color=COLORS["success"], width=80).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=pts_display, font=FONTS["body"], text_color=COLORS["primary"], width=100).pack(side="left", padx=2)
                
                pm_text = "เงินสด" if sale['payment_method'] == 'cash' else "โอน/QR"
                if sale['payment_method'] == 'mixed': pm_text = "ผสม"
                ctk.CTkLabel(row, text=pm_text, font=FONTS["body"], width=70).pack(side="left", padx=2)
                
                ctk.CTkLabel(row, text=sale['cashier_name'] or '-', font=FONTS["small"], width=100).pack(side="left", padx=2)
                ctk.CTkLabel(row, text=sale['items_list'] or '-', font=FONTS["small"], width=180, anchor="w").pack(side="left", padx=2)
                
        ctk.CTkButton(dialog, text="ปิดหน้าต่าง", font=FONTS["button"], width=150, height=40, command=dialog.destroy).pack(pady=15)
