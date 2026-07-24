# -*- coding: utf-8 -*-
"""
หน้าจัดการผู้ใช้งาน
"""

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
from config import *
import bcrypt


class UsersManagementFrame(ctk.CTkFrame):
    """Frame สำหรับจัดการผู้ใช้งาน"""
    
    def __init__(self, parent, user_id, current_role):
        super().__init__(parent, fg_color=COLORS["light"])
        self.user_id = user_id
        self.current_role = current_role
        self.db = DatabaseManager()
        
        # ตรวจสอบสิทธิ์
        if current_role not in ['admin', 'manager']:
            self.show_no_permission()
            return
        
        self.create_widgets()
        self.load_users()
        
    def show_no_permission(self):
        """แสดงข้อความไม่มีสิทธิ์"""
        ctk.CTkLabel(
            self,
            text="⚠️ คุณไม่มีสิทธิ์เข้าถึงหน้านี้",
            font=FONTS["heading"],
            text_color=COLORS["danger"]
        ).pack(expand=True)
        
    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text="👥 จัดการผู้ใช้งาน",
            font=FONTS["title"],
            text_color=COLORS["primary"]
        )
        title.pack(side="left")
        
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 รีเฟรช",
            font=FONTS["button"],
            width=120,
            height=40,
            fg_color=COLORS["info"],
            command=self.load_users
        )
        refresh_btn.pack(side="left", padx=5)
        
        add_btn = ctk.CTkButton(
            btn_frame,
            text="➕ เพิ่มผู้ใช้ใหม่",
            font=FONTS["button"],
            width=140,
            height=40,
            fg_color=COLORS["success"],
            command=self.add_user
        )
        add_btn.pack(side="left", padx=5)
        
        # สถิติ
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.total_users_card = self.create_stat_card(
            stats_frame, "👥 ผู้ใช้ทั้งหมด", "0", COLORS["info"]
        )
        self.total_users_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.active_users_card = self.create_stat_card(
            stats_frame, "✅ ใช้งานอยู่", "0", COLORS["success"]
        )
        self.active_users_card.pack(side="left", fill="x", expand=True, padx=5)
        
        self.inactive_users_card = self.create_stat_card(
            stats_frame, "❌ ระงับการใช้งาน", "0", COLORS["danger"]
        )
        self.inactive_users_card.pack(side="left", fill="x", expand=True, padx=5)
        
        # ตารางผู้ใช้
        table_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Header ตาราง
        header_row = ctk.CTkFrame(table_frame, fg_color=COLORS["primary"])
        header_row.pack(fill="x")
        
        headers = [
            ("ID", 60),
            ("ชื่อผู้ใช้", 150),
            ("ชื่อ-นามสกุล", 200),
            ("บทบาท", 150),
            ("อีเมล", 200),
            ("โทรศัพท์", 120),
            ("สถานะ", 100),
            ("จัดการ", 180)
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
        self.users_container = ctk.CTkScrollableFrame(
            table_frame,
            fg_color="white"
        )
        self.users_container.pack(fill="both", expand=True)
    
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
    
    def load_users(self):
        """โหลดรายการผู้ใช้"""
        # ล้างรายการเดิม
        for widget in self.users_container.winfo_children():
            widget.destroy()
        
        # ดึงข้อมูล
        self.db.connect()
        users = self.db.fetch_all("""
            SELECT user_id, username, full_name, role, email, phone, is_active, created_at
            FROM users
            ORDER BY user_id
        """)
        self.db.disconnect()
        
        # คำนวณสถิติ
        total = len(users)
        active = sum(1 for u in users if u['is_active'] == 1)
        inactive = total - active
        
        self.total_users_card.value_label.configure(text=str(total))
        self.active_users_card.value_label.configure(text=str(active))
        self.inactive_users_card.value_label.configure(text=str(inactive))
        
        # แสดงรายการ
        for idx, user in enumerate(users):
            self.create_user_row(user, idx)
    
    def create_user_row(self, user, index):
        """สร้างแถวผู้ใช้"""
        bg_color = COLORS["light"] if index % 2 == 0 else "white"
        
        row = ctk.CTkFrame(self.users_container, fg_color=bg_color, height=60)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # ID
        ctk.CTkLabel(
            row,
            text=str(user['user_id']),
            font=FONTS["body"],
            width=60
        ).pack(side="left", padx=5)
        
        # ชื่อผู้ใช้
        ctk.CTkLabel(
            row,
            text=user['username'],
            font=FONTS["body"],
            width=150
        ).pack(side="left", padx=5)
        
        # ชื่อ-นามสกุล
        ctk.CTkLabel(
            row,
            text=user['full_name'],
            font=FONTS["body"],
            width=200,
            anchor="w"
        ).pack(side="left", padx=5)
        
        # บทบาท
        role_text = USER_ROLES.get(user['role'], user['role'])
        ctk.CTkLabel(
            row,
            text=role_text,
            font=FONTS["body"],
            width=150
        ).pack(side="left", padx=5)
        
        # อีเมล
        ctk.CTkLabel(
            row,
            text=user['email'] or '-',
            font=FONTS["body"],
            width=200,
            anchor="w"
        ).pack(side="left", padx=5)
        
        # โทรศัพท์
        ctk.CTkLabel(
            row,
            text=user['phone'] or '-',
            font=FONTS["body"],
            width=120
        ).pack(side="left", padx=5)
        
        # สถานะ
        if user['is_active']:
            status_text = "✅ ใช้งาน"
            status_color = COLORS["success"]
        else:
            status_text = "❌ ระงับ"
            status_color = COLORS["danger"]
        
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
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=180)
        btn_frame.pack(side="left", padx=5)
        btn_frame.pack_propagate(False)
        
        # ปุ่มแก้ไข
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏️",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["info"],
            command=lambda u=user: self.edit_user(u)
        )
        edit_btn.pack(side="left", padx=2)
        
        # ปุ่มเปลี่ยนรหัสผ่าน
        pwd_btn = ctk.CTkButton(
            btn_frame,
            text="🔑",
            font=("Arial", 16),
            width=40,
            height=35,
            fg_color=COLORS["warning"],
            command=lambda u=user: self.change_password(u)
        )
        pwd_btn.pack(side="left", padx=2)
        
        # ปุ่มสถานะ
        if user['user_id'] != self.user_id:  # ไม่ให้ระงับตัวเอง
            if user['is_active']:
                status_btn = ctk.CTkButton(
                    btn_frame,
                    text="🚫",
                    font=("Arial", 16),
                    width=40,
                    height=35,
                    fg_color=COLORS["danger"],
                    command=lambda u=user: self.toggle_status(u)
                )
            else:
                status_btn = ctk.CTkButton(
                    btn_frame,
                    text="✅",
                    font=("Arial", 16),
                    width=40,
                    height=35,
                    fg_color=COLORS["success"],
                    command=lambda u=user: self.toggle_status(u)
                )
            status_btn.pack(side="left", padx=2)
    
    def add_user(self):
        """เพิ่มผู้ใช้ใหม่"""
        self.show_user_dialog(None)
    
    def edit_user(self, user):
        """แก้ไขผู้ใช้"""
        self.show_user_dialog(user)
    
    def show_user_dialog(self, user=None):
        """แสดง Dialog เพิ่ม/แก้ไขผู้ใช้"""
        dialog = ctk.CTkToplevel(self)
        
        if user:
            dialog.title(f"แก้ไขผู้ใช้ - {user['username']}")
        else:
            dialog.title("เพิ่มผู้ใช้ใหม่")
        
        dialog.geometry(get_responsive_dialog_geometry(self, 550, 620))
        dialog.transient(self)
        dialog.grab_set()
        
        # ฟอร์ม
        form_frame = ctk.CTkScrollableFrame(dialog, fg_color="white")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        fields = []
        
        # ชื่อผู้ใช้
        ctk.CTkLabel(form_frame, text="ชื่อผู้ใช้: *", font=FONTS["body"]).pack(anchor="w", pady=(10, 5))
        username_entry = ctk.CTkEntry(form_frame, font=FONTS["body"], height=40)
        username_entry.pack(fill="x", pady=(0, 10))
        if user:
            username_entry.insert(0, user['username'])
            username_entry.configure(state="disabled")  # ไม่ให้แก้ username
        fields.append(("username", username_entry))
        
        # รหัสผ่าน (เฉพาะเพิ่มใหม่)
        if not user:
            ctk.CTkLabel(form_frame, text="รหัสผ่าน: *", font=FONTS["body"]).pack(anchor="w", pady=(0, 5))
            password_entry = ctk.CTkEntry(form_frame, font=FONTS["body"], height=40, show="*")
            password_entry.pack(fill="x", pady=(0, 10))
            fields.append(("password", password_entry))
            
            ctk.CTkLabel(form_frame, text="ยืนยันรหัสผ่าน: *", font=FONTS["body"]).pack(anchor="w", pady=(0, 5))
            confirm_password_entry = ctk.CTkEntry(form_frame, font=FONTS["body"], height=40, show="*")
            confirm_password_entry.pack(fill="x", pady=(0, 10))
            fields.append(("confirm_password", confirm_password_entry))
        
        # ชื่อ-นามสกุล
        ctk.CTkLabel(form_frame, text="ชื่อ-นามสกุล: *", font=FONTS["body"]).pack(anchor="w", pady=(0, 5))
        fullname_entry = ctk.CTkEntry(form_frame, font=FONTS["body"], height=40)
        fullname_entry.pack(fill="x", pady=(0, 10))
        if user:
            fullname_entry.insert(0, user['full_name'])
        fields.append(("full_name", fullname_entry))
        
        # บทบาท
        ctk.CTkLabel(form_frame, text="บทบาท: *", font=FONTS["body"]).pack(anchor="w", pady=(0, 5))
        role_var = ctk.StringVar(value=user['role'] if user else "cashier")
        role_combo = ctk.CTkComboBox(
            form_frame,
            values=list(USER_ROLES.values()),
            font=FONTS["body"],
            height=40,
            variable=role_var
        )
        role_combo.pack(fill="x", pady=(0, 10))
        fields.append(("role", role_var))
        
        # อีเมล
        ctk.CTkLabel(form_frame, text="อีเมล:", font=FONTS["body"]).pack(anchor="w", pady=(0, 5))
        email_entry = ctk.CTkEntry(form_frame, font=FONTS["body"], height=40)
        email_entry.pack(fill="x", pady=(0, 10))
        if user and user['email']:
            email_entry.insert(0, user['email'])
        fields.append(("email", email_entry))
        
        # โทรศัพท์
        ctk.CTkLabel(form_frame, text="โทรศัพท์:", font=FONTS["body"]).pack(anchor="w", pady=(0, 5))
        phone_entry = ctk.CTkEntry(form_frame, font=FONTS["body"], height=40)
        phone_entry.pack(fill="x", pady=(0, 10))
        if user and user['phone']:
            phone_entry.insert(0, user['phone'])
        fields.append(("phone", phone_entry))
        
        # ปุ่ม
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save():
            # รวบรวมข้อมูล
            data = {}
            for field_name, field_widget in fields:
                if isinstance(field_widget, ctk.StringVar):
                    value = field_widget.get()
                else:
                    value = field_widget.get().strip()
                data[field_name] = value
            
            # ตรวจสอบ
            if not user and not data.get('username'):
                messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกชื่อผู้ใช้")
                return
            
            if not user:
                if not data.get('password'):
                    messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกรหัสผ่าน")
                    return
                if data['password'] != data.get('confirm_password'):
                    messagebox.showerror("ข้อผิดพลาด", "รหัสผ่านไม่ตรงกัน")
                    return
            
            if not data.get('full_name'):
                messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกชื่อ-นามสกุล")
                return
            
            # แปลง role จากชื่อไทยเป็น key
            role_thai_to_key = {v: k for k, v in USER_ROLES.items()}
            role_key = role_thai_to_key.get(data['role'], 'cashier')
            
            self.db.connect()
            
            try:
                if user:
                    # แก้ไข
                    self.db.execute("""
                        UPDATE users
                        SET full_name = ?, role = ?, email = ?, phone = ?
                        WHERE user_id = ?
                    """, (
                        data['full_name'],
                        role_key,
                        data['email'] if data['email'] else None,
                        data['phone'] if data['phone'] else None,
                        user['user_id']
                    ))
                    messagebox.showinfo("สำเร็จ", "แก้ไขข้อมูลผู้ใช้สำเร็จ")
                else:
                    # เพิ่มใหม่
                    password_hash = bcrypt.hashpw(
                        data['password'].encode('utf-8'),
                        bcrypt.gensalt()
                    ).decode('utf-8')
                    
                    self.db.execute("""
                        INSERT INTO users (username, password_hash, full_name, role, email, phone, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (
                        data['username'],
                        password_hash,
                        data['full_name'],
                        role_key,
                        data['email'] if data['email'] else None,
                        data['phone'] if data['phone'] else None
                    ))
                    messagebox.showinfo("สำเร็จ", "เพิ่มผู้ใช้ใหม่สำเร็จ")
                
                self.db.disconnect()
                dialog.destroy()
                self.load_users()
                
            except Exception as e:
                self.db.disconnect()
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกได้: {e}")
        
        ctk.CTkButton(
            btn_frame,
            text="💾 บันทึก",
            font=("Sarabun", 16, "bold"),
            width=150,
            height=45,
            fg_color=COLORS["success"],
            command=save
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
    
    def change_password(self, user):
        """เปลี่ยนรหัสผ่าน"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"เปลี่ยนรหัสผ่าน - {user['username']}")
        dialog.geometry(get_responsive_dialog_geometry(self, 450, 350))
        dialog.transient(self)
        dialog.grab_set()
        
        # ข้อมูลผู้ใช้
        info_frame = ctk.CTkFrame(dialog, fg_color=COLORS["light"], corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            info_frame,
            text=f"ผู้ใช้: {user['full_name']} ({user['username']})",
            font=FONTS["body"]
        ).pack(padx=20, pady=20)
        
        # รหัสผ่านใหม่
        ctk.CTkLabel(
            dialog,
            text="รหัสผ่านใหม่:",
            font=FONTS["body"]
        ).pack(pady=(10, 5))
        
        password_entry = ctk.CTkEntry(
            dialog,
            font=FONTS["body"],
            height=45,
            show="*"
        )
        password_entry.pack(fill="x", padx=20, pady=5)
        password_entry.focus()
        
        # ยืนยันรหัสผ่าน
        ctk.CTkLabel(
            dialog,
            text="ยืนยันรหัสผ่านใหม่:",
            font=FONTS["body"]
        ).pack(pady=(10, 5))
        
        confirm_entry = ctk.CTkEntry(
            dialog,
            font=FONTS["body"],
            height=45,
            show="*"
        )
        confirm_entry.pack(fill="x", padx=20, pady=5)
        
        # ปุ่ม
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def save_password():
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not password:
                messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกรหัสผ่านใหม่")
                return
            
            if len(password) < 4:
                messagebox.showerror("ข้อผิดพลาด", "รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร")
                return
            
            if password != confirm:
                messagebox.showerror("ข้อผิดพลาด", "รหัสผ่านไม่ตรงกัน")
                return
            
            # เข้ารหัสและบันทึก
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            self.db.connect()
            self.db.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ?",
                (password_hash, user['user_id'])
            )
            self.db.disconnect()
            
            messagebox.showinfo("สำเร็จ", "เปลี่ยนรหัสผ่านสำเร็จ")
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="🔑 เปลี่ยนรหัสผ่าน",
            font=("Sarabun", 16, "bold"),
            width=180,
            height=45,
            fg_color=COLORS["warning"],
            command=save_password
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
    
    def toggle_status(self, user):
        """เปลี่ยนสถานะผู้ใช้"""
        if user['is_active']:
            action = "ระงับการใช้งาน"
            new_status = 0
        else:
            action = "เปิดใช้งาน"
            new_status = 1
        
        result = messagebox.askyesno(
            "ยืนยัน",
            f"ต้องการ{action}ผู้ใช้ '{user['full_name']}' หรือไม่?"
        )
        
        if result:
            self.db.connect()
            self.db.execute(
                "UPDATE users SET is_active = ? WHERE user_id = ?",
                (new_status, user['user_id'])
            )
            self.db.disconnect()
            
            messagebox.showinfo("สำเร็จ", f"{action}สำเร็จ")
            self.load_users()
