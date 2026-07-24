# เอกสารสรุปงานปรับปรุงระบบ Responsive UI & License System (Store POS)
**วันที่อัปเดต:** 24 กรกฎาคม 2026  
**เวอร์ชัน:** Store POS (เวอร์ชันเต็ม - Full Version)

---

## 📌 1. ภาพรวมของงานที่ได้ดำเนินการ (Executive Summary)

เอกสารฉบับนี้จัดทำขึ้นเพื่อบันทึกโครงสร้าง โค้ดที่มีการแก้ไข และแนวทางการไล่บั๊ก (Debugging Guide) สำหรับงานปรับปรุง 2 ส่วนหลัก:
1. **Full Responsive UI**: การปรับแต่งหน้าจอทุกส่วนของโปรแกรมเวอร์ชันเต็ม ให้สามารถขยาย/ย่อขนาดตามความละเอียดจอคอมพิวเตอร์อย่างสมบูรณ์แบบ โดยเฉพาะจอมอนิเตอร์รุ่นเก่า หรือจอความละเอียดประมาณ **1300 x 700 / 1366 x 768 / 1280 x 720 / 1024 x 768** ไม่ให้ปุ่มสำคัญ (เช่น ปุ่มชำระเงิน F10, ยอดสุทธิ, ปุ่มบันทึก) หลุดขอบล่างของจอภาพ
2. **License System & Admin KeyGen Tools**: การแก้ไขปุ่ม Activate ค้าง, การเพิ่มระบบกำหนดจำนวนวันตามใจคนขาย (Custom Expiry Days) และระบบการรีเซ็ต License ให้ย้อนกลับสู่หน้า Activate ได้จริงทั้งในแอปหลักและในเครื่องมือ KeyGen

---

## 📐 2. รายละเอียดการปรับปรุง Responsive UI (โครงสร้างและไฟล์ที่แก้ไข)

### 2.1 ไฟล์ศูนย์กลางคอนฟิก ([config.py](file:///c:/Users/admin/Documents/store-pos/config.py))
- **ปรับลด `MIN_WINDOW_SIZE`**: จาก `(1200, 700)` เหลือ `(1000, 560)` เพื่อยอมให้หน้าต่างหดขนาดได้อย่างปลอดภัยบนจอความละเอียดต่ำ
- **เพิ่ม Helper Function `get_responsive_dialog_geometry(parent, target_w, target_h)`**:
  - สแกนความสูงหน้าจอจริง (`screen_height`)
  - คำนวณความสูงสูงสุดให้อยู่ในกรอบ `screen_height - 60px` (เพื่อเว้นพื้นที่ Taskbar ของ Windows)
  - จัดตำแหน่ง X, Y ให้อยู่กึ่งกลางหน้าจออัตโนมัติ โดยป้องกันไม่ให้ค่า X, Y ติดลบ (`x = max(0, ...), y = max(0, ...)`)

### 2.2 หน้าต่างหลักและเมนูซ้าย ([ui/main_window.py](file:///c:/Users/admin/Documents/store-pos/ui/main_window.py))
- **Auto-Maximized**: เพิ่มระบบตรวจจับขนาดจอตอนเริ่มต้น หากกว้าง <= 1366px หรือสูง <= 768px จะสั่งเปิดหน้าต่างแบบขยายเต็มจอ (`zoomed`) อัตโนมัติ
- **Header**: ลดความสูงจาก `70px` เหลือ `50px` (ปรับขนาดฟอนต์หัวข้อเป็น 18pt bold)
- **Sidebar**: ลดความกว้างแผงซ้ายจาก `250px` เหลือ `220px` และลดความสูงปุ่มเมนูจาก `50px` เหลือ `38px` (ฟอนต์ 14pt bold) ช่วยให้เมนูทั้งหมด 11 รายการรวมปุ่ม Logout แสดงผลพอดีแนวตั้งบนจอ 700px โดยไม่หลุดขอบล่าง

### 2.3 หน้าขายสินค้า POS ([ui/pos_window.py](file:///c:/Users/admin/Documents/store-pos/ui/pos_window.py))
- **Cart Scrollable List**: ยกเลิกการล็อกความสูงคงที่ `height=300` ของ `cart_list` เปลี่ยนเป็น Dynamic Scrollable Frame (`fill="both", expand=True`) ยืดหดตามขนาดความสูงหน้าจอจริง
- **แผงสรุปยอดเงินฝั่งขวา**: ปรับลดขนาดฟอนต์ยอดสุทธิจาก `48pt` เหลือ `32pt bold` และปรับลด padding ของแผงสรุป
- **ปุ่มชำระเงิน F10**: ปรับลดความสูงจาก `60px` เหลือ `48px` ตรึงตำแหน่งไว้ที่ขอบล่างสุดของแผงขวาเสมอ
- **Checkout Dialog**: ปรับมาใช้ `get_responsive_dialog_geometry(self, 520, target_h)`

### 2.4 หน้าต่าง Dialog ทั้งหมดในระบบ
ทุก Dialog ถูกเปลี่ยนจากการตั้งขนาด `geometry("W x H")` แบบคงที่ มาผ่าน `get_responsive_dialog_geometry()`:
- [ui/product_window.py](file:///c:/Users/admin/Documents/store-pos/ui/product_window.py): ฟอร์มสินค้า (`750x780` capped), พิมพ์บาร์โค้ดแบบกลุ่ม (`980x640`)
- [ui/member_window.py](file:///c:/Users/admin/Documents/store-pos/ui/member_window.py): ฟอร์มสมาชิก (`600x580`), ปรับแต้ม/เครดิต (`450x420`), ตั้งค่า Tier (`600x500`), เพิ่ม Tier (`400x300`), ประวัติสมาชิก (`850x600`)
- [ui/users_window.py](file:///c:/Users/admin/Documents/store-pos/ui/users_window.py): ฟอร์มผู้ใช้ (`550x620`), เปลี่ยนรหัสผ่าน (`450x350`)
- [ui/history_window.py](file:///c:/Users/admin/Documents/store-pos/ui/history_window.py): ดูรายละเอียดบิล (`720x620`)
- [ui/activation_window.py](file:///c:/Users/admin/Documents/store-pos/ui/activation_window.py): หน้าต่าง Activate (`700x620`)
- [ui/login_window.py](file:///c:/Users/admin/Documents/store-pos/ui/login_window.py): จัดตำแหน่งกลางจอโดยใช้ `max(0, y)` ป้องกันขอบบนหลุดจอ

---

## 🔑 3. รายละเอียดการปรับปรุงระบบ License & KeyGen Tools

### 3.1 การแก้ไขบั๊กกด Activate แล้วค้าง
- **สาเหตุเดิม**: ใน `ActivationWindow` มีการใส่ `self.attributes("-topmost", True)` ซ้อนกับ `self.grab_set()` ทำให้เมื่อกดปุ่ม Activate กล่องข้อความ native `messagebox.showinfo()` ถูกบังอยู่หลังหน้าต่าง Activation และไม่ได้รับ Focus ผู้ใช้จึงกด OK ไม่ได้ ทำให้โปรแกรมค้างรอกด OK และไม่ยอมรันบรรทัด `self.destroy()`
- **การแก้ไข**: 
  - ถอด `attributes("-topmost", True)` ออกจาก `ActivationWindow`
  - กำหนด `parent=self` ให้กับทุก MessageBox ใน `ActivationWindow`
  - สั่ง `self.grab_release()` ก่อนเปิด MessageBox เพื่อคืน Focus ให้ Dialog เสมอ

### 3.2 การปรับวันตามใจคนขาย (Custom Expiry Days)
- **ไฟล์ที่ปรับปรุง**: [keygen_standalone.py](file:///c:/Users/admin/Documents/store-pos/keygen_standalone.py), [tools/keygen_standalone.py](file:///c:/Users/admin/Documents/store-pos/tools/keygen_standalone.py), [tools/license_generator.py](file:///c:/Users/admin/Documents/store-pos/tools/license_generator.py)
- **กลไก**: ตั้งค่า `self.expire_combo` เป็น `state="normal"` อนุญาตให้คนขายพิมพ์ตัวเลขจำนวนวันได้เองอย่างอิสระ (เช่น พิมพ์ `45`, `60`, `100`, `500`) และใช้ Regex `re.findall(r'\d+', expire_str)` สกัดตัวเลขจำนวนวันไปคำนวณวันหมดอายุ `(now + timedelta(days=expire_days))`

### 3.3 การรีเซ็ต License คืนกลับสู่หน้า Activate
- **[utils/license_system.py](file:///c:/Users/admin/Documents/store-pos/utils/license_system.py)**: อัปเดต `LicenseManager.delete_license()` ให้ค้นหาและลบไฟล์ `.license` จากทุกตำแหน่งในเครื่อง พร้อมล้างค่า `last_run_timestamp` และ `trial_start_date` ออกจากตาราง `settings` ในฐานข้อมูล SQLite
- **[ui/settings_window.py](file:///c:/Users/admin/Documents/store-pos/ui/settings_window.py)**: เพิ่มปุ่ม **`🧹 รีเซ็ตสิทธิ์ (กลับหน้า Activate)`** ในแท็บ *"สิทธิ์การใช้งาน"* เมื่อกดจะลบสิทธิ์และเปิด `ActivationWindow` ขึ้นมาให้ลงทะเบียนใหม่ได้จากภายในโปรแกรมทันที
- **KeyGen Tools**: เพิ่มปุ่ม **`🚀 รีเซ็ตสิทธิ์ & เปิดหน้า Activate ทันที`** สั่งปิด POS ค้างในระบบ ลบสิทธิ์ และสั่งเปิด `main.py` เข้าสู่หน้า Activate ใหม่ทันที

---

## 🛠️ 4. คู่มือการติดตามและแก้บั๊กในอนาคต (Debugging & Troubleshooting Guide)

### 🐛 กรณีที่ 1: ปุ่มหรือเนื้อหาใน Dialog ล้นหลุดขอบล่างบนจอเล็ก
1. **จุดที่ต้องเช็ค**: ตรวจสอบการตั้งขนาด geometry ในไฟล์ GUI ของหน้านั้นๆ
2. **วิธีแก้**: ห้ามใช้ `dialog.geometry("WxH")` แบบ fixed พิกเซล ให้เปลี่ยนเป็น `dialog.geometry(get_responsive_dialog_geometry(parent, target_w, target_h))`
3. **เนื้อหาฟอร์มที่มีหลายแถว**: ต้องหุ้มด้วย `ctk.CTkScrollableFrame` เสมอ เพื่อให้มี Scrollbar เลื่อนได้หากความสูงหน้าจอน้อยกว่าปกติ

### 🐛 กรณีที่ 2: กดปุ่มแจ้งเตือน/บันทึก แล้วโปรแกรมค้าง นิ่ง ไม่ยอมปิดหน้าต่าง
1. **จุดที่ต้องเช็ค**: ตรวจสอบว่าใน `CTkToplevel` หน้าต่างนั้น มีการสั่ง `self.attributes("-topmost", True)` ไว้หรือไม่
2. **วิธีแก้**:
   - ลบ `-topmost` ออก เพราะ `-topmost` จะกั้น native dialog (เช่น `messagebox` หรือ `filedialog`) ไม่ให้ลอยขึ้นมาข้างหน้า
   - เมื่อจะเรียก `messagebox` ให้ระบุ `parent=self` เสมอ เช่น `messagebox.showinfo(title, msg, parent=self)`

### 🐛 กรณีที่ 3: รีเซ็ต License แล้ว แต่เปิดโปรแกรมใหม่ยังไม่ขึ้นหน้า Activate
1. **จุดที่ต้องเช็ค**:
   - ตรวจสอบว่าไฟล์ `.license` ที่ `c:\Users\admin\Documents\store-pos\data\.license` หรือในโฟลเดอร์โปรแกรมถูกลบจริงหรือไม่
   - ตรวจสอบใน SQLite `data/database.db` ตาราง `settings` ว่ามี `last_run_timestamp` ค้างอยู่หรือไม่
2. **วิธีแก้**: เรียกใช้ `LicenseManager.delete_license()` หรือใช้ปุ่ม `🧹 ล้างความจำเครื่อง (Reset Activation & DB)` จาก [keygen_standalone.py](file:///c:/Users/admin/Documents/store-pos/keygen_standalone.py)

---

## 📁 5. สรุปรายการไฟล์สำคัญในโปรเจค
- [config.py](file:///c:/Users/admin/Documents/store-pos/config.py) — ศูนย์กลางคอนฟิก & Responsive Helper (`get_responsive_dialog_geometry`)
- [main.py](file:///c:/Users/admin/Documents/store-pos/main.py) — Entry point หลักของเวอร์ชันเต็ม
- [ui/main_window.py](file:///c:/Users/admin/Documents/store-pos/ui/main_window.py) — หน้าต่างหลัก การขยายเต็มจอ (Zoomed) และโครงสร้าง Header/Sidebar
- [ui/pos_window.py](file:///c:/Users/admin/Documents/store-pos/ui/pos_window.py) — หน้าขายสินค้า POS และ Checkout Dialog
- [ui/activation_window.py](file:///c:/Users/admin/Documents/store-pos/ui/activation_window.py) — หน้าต่าง Activate โปรแกรม (แก้ไข Modal Focus)
- [ui/settings_window.py](file:///c:/Users/admin/Documents/store-pos/ui/settings_window.py) — หน้าตั้งค่า และแท็บสิทธิ์การใช้งาน (เพิ่มปุ่มรีเซ็ตสิทธิ์)
- [utils/license_system.py](file:///c:/Users/admin/Documents/store-pos/utils/license_system.py) — ระบบตรวจสอบ/บันทึก/ลบ License Key
- [keygen_standalone.py](file:///c:/Users/admin/Documents/store-pos/keygen_standalone.py) — เครื่องมือสร้างคีย์และดูแลระบบสิทธิ์สำหรับ Admin/ผู้ขาย (Custom Expiry Days & Reset License)

---

## 🔒 6. การแก้ไขบั๊กโฟลเดอร์ `_internal` ล็อคค้าง (Process Zombie & File Lock)

### 6.1 สาเหตุของการล็อกไฟล์
- เมื่อแอปพลิเคชันถูกรันจากชุดโฟลเดอร์ PyInstaller (One-folder mode) บนระบบปฏิบัติการ Windows ตัวเรียกโปรแกรมจะมีการโหลด Dynamic Link Libraries (DLLs) และปลั๊กอินไบนารี (`.pyd` และ `.dll`) จากโฟลเดอร์ `_internal` เข้าสู่หน่วยความจำ
- การสั่งออกโปรแกรมด้วย `sys.exit(0)` ในบางสภาพแวดล้อม (เช่น มี Thread ค้าง หรือ Tkinter mainloop ยังเคลียร์ handler ไม่หมด) จะทำให้ Process ของ Python กลายเป็นสถานะ **Zombie** ที่แฝงอยู่ในพื้นหลังของ Task Manager และถือครองไฟล์ล็อคเหล่านั้นอยู่ ส่งผลให้โฟลเดอร์ `_internal` ไม่สามารถแก้ไขหรือลบได้ จนกว่าจะ Reboot เครื่องคอมพิวเตอร์

### 6.2 การแก้ไขแบบถาวร
1. **เพิ่มฟังก์ชัน `safe_exit` ใน [main.py](file:///c:/Users/admin/Documents/store-pos/main.py)**:
   ```python
   def safe_exit(code=0):
       try:
           cleanup_resources()
       except Exception:
           pass
       import os
       os._exit(code)
   ```
2. **เรียกใช้ `os._exit(0)`**: บังคับจบการทำงานของโปรเซสในระดับระบบปฏิบัติการ (OS-level termination) ทันทีหลังปล่อย UI และ Database connections ซึ่งจะคืนทรัพยากรทุกอย่างให้ Windows ปล่อย File Lock ทันที ทำให้สามารถสลับ/ลบโฟลเดอร์ `_internal` ได้ทันทีโดยไม่ต้อง Restart เครื่องคอมพิวเตอร์อีกต่อไป
3. **การใช้งาน**: ใช้ `safe_exit` ใน `main.py` ทุกจุดออก และปรับปรุงปุ่ม Logout ใน `ui/main_window.py` ให้เรียก `cleanup_resources()` และ `os._exit(0)`

