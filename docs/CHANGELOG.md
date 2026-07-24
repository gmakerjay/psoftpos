# Changelog

บันทึกการแก้ไขข้อผิดพลาดและการปรับปรุงระบบ (Bug Fixes & System Enhancements)

---

## [1.0.5] - 2026-07-22

### 🚀 1. แก้ไขปัญหา Splash Screen โหลดค้าง (Splash Screen Event Loop Stack Unrolling Fix)
* **ปัญหาที่พบ:** หน้า Splash Screen โหลดเข้าได้บ้างค้างบ้าง โดยเฉพาะตอนสลับเปิดหน้าต่าง Login เนื่องจากคำสั่ง `on_complete_callback` ถูกเรียกขณะที่ยังอยู่ภายใน Event Loop Callback (`after()`) ของ Splash Window ที่กำลังสั่ง `.quit()` และ `.destroy()` ทำให้ CustomTkinter เกิด Tcl Exception หรือติดขัดในลูป `check_dpi_scaling`
* **ไฟล์ที่แก้ไข:** [ui/splash_screen.py](file:///c:/Users/admin/Documents/store-pos/ui/splash_screen.py)
* **การแก้ไข:** 
  * ปรับปรุง `SplashScreen` ย้ายการเรียก `on_complete(results)` ให้ออกมารันนอก Event Loop Stack **หลังจาก `self.root.mainloop()` ถอนตัวออกอย่างสมบูรณ์**
  * ครอบ `update_progress` ด้วย `try...except (ctk.TclError, Exception)` ป้องกันข้อผิดพลาดจากการอัปเดต GUI ขณะปิดตัว

---

### ⚡ 2. ป้องกัน Infinite Recursion และปรับแต่ง Connection Pool (`database/db_manager.py`)
* **ปัญหาที่พบ:** `_check_and_auto_init()` มีการเรียก `initialize_database()` ซึ่งกลับมาเรียก `connect()` -> `_check_and_auto_init()` ซ้ำซ้อน และ Connection Pool ไม่ได้ตรวจ `db_path` ทำให้ instance สำหรับ temporary DB ดึง connection ของ DB หลักไปใช้
* **ไฟล์ที่แก้ไข:** [database/db_manager.py](file:///c:/Users/admin/Documents/store-pos/database/db_manager.py)
* **การแก้ไข:**
  * เพิ่ม Flag `_is_initializing` เพื่อป้องกันปัญหา Re-entry Loop ตอน Auto-initialize ตาราง
  * เพิ่มการตรวจสอบ `conn_info.get('db_path') == self.db_path` ใน Connection Pool
  * ปรับปรุง `close_all_connections()` ให้เคลียร์ WAL Log (`PRAGMA wal_checkpoint(TRUNCATE)`) และรีเซ็ต Class State `_schema_upgraded = False` และ `_is_initializing = False` ให้พร้อมสำหรับการสร้าง DB ใหม่ทันที

---

### 🔄 3. ปรับปรุงระบบ Hard Reset และระบบ Auto-Restart อัตโนมัติ (`ui/settings_window.py` & `utils/system_utils.py`)
* **ปัญหาที่พบ:** การทำ Hard Reset ในการตั้งค่าเพียงลบไฟล์ DB บนดิสก์ แต่เปิดหน้าต่างหลักค้างไว้ ทำให้คลิกทำงานต่อแล้วแครช และเมื่อรีสตาร์ทโปรแกรมใหม่ Class State `_schema_upgraded` ยังเป็น True ทำให้ข้ามการสร้างตารางบน DB ใหม่
* **ไฟล์ที่แก้ไข:** [ui/settings_window.py](file:///c:/Users/admin/Documents/store-pos/ui/settings_window.py), [utils/system_utils.py](file:///c:/Users/admin/Documents/store-pos/utils/system_utils.py), [utils/__init__.py](file:///c:/Users/admin/Documents/store-pos/utils/__init__.py), [main.py](file:///c:/Users/admin/Documents/store-pos/main.py), [main_trial_30days.py](file:///c:/Users/admin/Documents/store-pos/main_trial_30days.py)
* **การแก้ไข:**
  * สร้างโมดูล `utils/system_utils.py` รวมฟังก์ชัน `cleanup_resources()` และ `restart_application()`
  * ปรับปรุง `SettingsWindow.reset_system()` ให้เคลียร์ DB Connection, ลบไฟล์ DB ทุกตัว (`database.db`, `sales.db`, `-wal`, `-shm`), เคลียร์ State และสั่ง `restart_application()` อัตโนมัติทันที
  * โปรแกรมจะปิดตัว คืนทรัพยากร และรีสตาร์ทกระบวนการเปิดขึ้นมาใหม่โดยอัตโนมัติ (Splash Screen -> Auto-create DB -> Login Window) โดยไม่ค้าง

---

### 🧪 4. ระบบทดสอบยืนยันเสถียรภาพ (Verification Tests)
* **สิ่งที่ทำ:** สร้าง script `tests/test_splash_and_reset_verification.py` ยืนยันการสร้าง DB ใหม่จากไฟล์ว่างเปล่า และลำดับขั้นตอน Hard Reset ➔ Re-initialize ผลการทดสอบผ่าน 100% พร้อมทดสอบร่วมกับ `verify_license_system.py` (39/39 Passed)

---

## [1.0.4] - 2026-07-17

### 👥 1. ปรับปรุงระบบจัดการสมาชิกและระบบแต้มสะสมใหม่ (Simplified Member & Points System)
* **การปรับปรุง:**
  * อัปเกรดโครงสร้างฐานข้อมูลตาราง `members` (เพิ่ม `address` และ `privilege`) และตาราง `sales` (เพิ่ม `points_earned` และ `points_used`) โดยอัตโนมัติเมื่อเปิดโปรแกรม
  * ยุบรวมหน้าจัดการสมาชิก [ui/member_window.py](file:///c:/Users/admin/Documents/store-pos/ui/member_window.py) แสดงเฉพาะคอลัมน์สำคัญ: **ชื่อสมาชิก, เบอร์โทร, ที่อยู่, สิทธิพิเศษ, และแต้มสะสม**
  * ปรับฟอร์มเพิ่ม/แก้ไขสมาชิกให้ง่ายและเร็วขึ้น และให้ผู้ใช้แก้ไขแต้มสะสมปัจจุบันได้ทันทีจากฟอร์ม
  * เพิ่มช่องกรอกและระบบคำนวณแต้มสะสม / ใช้แต้มในหน้าชำระเงินของ [ui/pos_window.py](file:///c:/Users/admin/Documents/store-pos/ui/pos_window.py)
  * บันทึกประวัติการใช้แต้มและแต้มที่ได้รับย้อนหลัง พร้อมแสดงผลในตารางประวัติธุรกรรมสมาชิกย้อนหลัง (+แต้มที่ได้ / -แต้มที่ใช้)

### 🌿 2. เพิ่มกรอบโปรแกรมลายธรรมชาติแบบพรีเมียม (Premium App Window Natural Border)
* **สิ่งที่ทำ:**
  * สร้างรูปภาพขอบสไตล์ธรรมชาติสีเข้มลายไม้และใบไม้พรีเมียม [assets/app_border.png](file:///c:/Users/admin/Documents/store-pos/assets/app_border.png)
  * อัปเดตโครงสร้างหน้าต่าง [ui/main_window.py](file:///c:/Users/admin/Documents/store-pos/ui/main_window.py) ให้จัดวางรูปขอบเป็นพื้นหลังและขยายขนาดตามหน้าต่างอัตโนมัติ (Dynamic Resizing)
  * ปรับแต่งระยะห่าง (Padding) ของขอบหน้าต่างหลักและแผงหัวข้อขึ้น 10px ทำให้ขอบลายธรรมชาติล้อมรอบหน้าต่างโปรแกรมอย่างสวยงามเมื่อสลับใช้งานทุกๆ เมนู

### ⚡ 3. เพิ่มประสิทธิภาพและความจำสำหรับคอมพิวเตอร์สเปกต่ำ (Low-End PC Performance Optimizations)
* **สิ่งที่ทำ:**
  * นำค่าคอนฟิกจาก [performance_config.py](file:///c:/Users/admin/Documents/store-pos/performance_config.py) มาทำงานจริงในระบบหลังบ้าน:
    * จัดการหน่วยความจำ (Garbage Collection) อัตโนมัติในพื้นหลังทุกๆ 5 นาทีด้วย `gc.collect()`
    * ล้าง Cache สินค้าและ Cache รายชื่อสมาชิกหน้า POS ทันทีเมื่อผู้ใช้ย้ายหน้าต่างไปเมนูอื่น
    * ป้องกันปัญหาหน่วยความจำรั่วไหล (Memory Leak) จากการผูกเฟรม UI ที่ถูกทำลายไปแล้วด้วยการล้างตัวแปรอ้างอิง `_pos_frame` ทุกครั้งที่สลับหน้าต่างสำเร็จ
    * เพิ่มการเช็กหน้าต่างยังเปิดอยู่เพื่อป้องกันการสั่งอัปเดตเวลา (`update_time`) ค้างหลังจากปิดหน้าต่างหลักไปแล้ว ป้องกันการเกิดข้อผิดพลาด TclError ใน Console

### 🔑 4. แก้ไขบั๊กการคำนวณวันหมดอายุ License ผิดพลาดล่วงหน้า (License Date Lockout Bug Fix)
* **ปัญหาที่พบ:** การตรวจสอบวันหมดอายุแบบละเอียดระดับวินาทีของเดิมส่งผลให้เหลือวันใช้งานจริงเป็น `0` วันในวันสุดท้ายปฏิทิน และระบบสั่งแสดงคำเตือนระดับ `'expired'` ล็อกการเข้าใช้งานของลูกค้าก่อนเวลาหมดอายุจริง 1 วัน
* **สิ่งที่ทำ:** ปรับการคำนวณใน [utils/license_system.py](file:///c:/Users/admin/Documents/store-pos/utils/license_system.py) ให้คิดระดับวันปฏิทิน (`date`) และขยับเงื่อนไขล็อกโปรแกรมให้อนุญาตใช้งานในวันสุดท้ายได้ (ล็อกสิทธิ์เมื่อวันคงเหลือ `< 0` วัน)
* **การตรวจสอบ:** พัฒนาสคริปต์ programmatic verification [verify_license_system.py](file:///c:/Users/admin/Documents/store-pos/scratch/verify_license_system.py) ปรับปรุงให้ดักจับ sys.modules ครอบคลุม และผ่านการทดสอบ 39/39 การตรวจสอบสำเร็จ

---

## [1.0.3] - 2026-07-17

### 🔐 1. ปรับปรุงระบบ License & Activation ให้สมบูรณ์ (License System Enhancement)
* **การปรับปรุง:**
  * ตรวจสอบและยืนยันว่า `get_expiry_warning()` ใน `license_system.py` มี `try/except` ครบถ้วน ไม่มี syntax error
  * ระบบ Activation ทำงานถูกต้อง: ตรวจสอบ License → แสดงหน้า HWID เมื่อยังไม่ Activate → ข้ามไป Login เมื่อ Activate แล้ว
  * ระบบแจ้งเตือน License หมดอายุ ทำงานแบ่งระดับตามประเภท License (ทดสอบ/ระยะสั้น/ระยะยาว) ถูกต้อง
* **ไฟล์ที่เกี่ยวข้อง:** [utils/license_system.py](file:///c:/Users/admin/Documents/store-pos/utils/license_system.py), [ui/activation_window.py](file:///c:/Users/admin/Documents/store-pos/ui/activation_window.py)

---

### 🔑 2. สร้าง Standalone KeyGen Tool — ไฟล์เดียวย้ายได้ทุกเครื่อง (Standalone License Key Generator)
* **สิ่งที่ทำ:**
  * สร้างไฟล์ `keygen_standalone.py` ที่รวม **HardwareID + LicenseManager + GUI** ไว้ในไฟล์เดียว
  * **ไม่ต้องพึ่ง** `database`, `utils`, `config` หรือ module ใดๆ จาก project หลัก
  * ใช้ SECRET_KEY ตรงกับ project หลัก ทำให้ License Key ที่สร้างใช้งานกับ POS ได้ทันที
  * รองรับ GUI Mode (customtkinter) และ **CLI Mode** (fallback อัตโนมัติเมื่อไม่มี GUI)
  * ฟีเจอร์ครบ: สร้าง License, ตรวจสอบ, ถอดรหัส, ดู HWID, สร้าง License ทดสอบ 1 วัน
  * สร้าง `build_keygen.spec` สำหรับ build เป็น .exe ด้วย PyInstaller
* **ไฟล์ใหม่:** [keygen_standalone.py](file:///c:/Users/admin/Documents/store-pos/keygen_standalone.py), [build_keygen.spec](file:///c:/Users/admin/Documents/store-pos/build_keygen.spec)

---

### 🗑️ 3. เพิ่มปุ่ม "ล้าง License เครื่องนี้" ในเครื่องมือผู้ขาย (Clear License Tool for Testing)
* **สิ่งที่ทำ:**
  * เพิ่มปุ่ม **"🗑️ ล้าง License เครื่องนี้ (สำหรับทดสอบ)"** ในส่วนเครื่องมือผู้ขายทั้ง 2 ไฟล์
  * มีระบบยืนยันก่อนลบ (Confirm Dialog) แสดง path ของไฟล์และคำเตือน
  * หลังจากลบ License จะแสดงผลลัพธ์พร้อมคำแนะนำขั้นตอนถัดไป
  * เมื่อเปิดโปรแกรม POS ครั้งถัดไป จะแสดงหน้า Activation (HWID) ใหม่
* **ไฟล์ที่แก้ไข:** [license_generator.py](file:///c:/Users/admin/Documents/store-pos/license_generator.py), [keygen_standalone.py](file:///c:/Users/admin/Documents/store-pos/keygen_standalone.py)

---

### 📦 4. Build Production และแพ็คไฟล์พร้อมส่งมอบ (Production Build & Packaging)
* **สิ่งที่ทำ:**
  * Build โปรแกรม POS หลัก (`StorePOS.exe`) ด้วย PyInstaller 6.20.0 + Python 3.12.10
  * Build เครื่องมือ KeyGen (`KeyGen.exe`) แยกต่างหาก — ขนาดเบา (~2.8 MB)
  * จัดโครงสร้างโฟลเดอร์ `PsotStore` บน Desktop พร้อมส่งมอบ:
    ```
    PsotStore/
    ├── Program/           ← โปรแกรม POS (StorePOS.exe + dependencies)
    │   ├── StorePOS.exe
    │   ├── _internal/
    │   ├── data/
    │   │   ├── database.db
    │   │   └── products/
    │   ├── Backup/
    │   ├── Logs/
    │   └── Excel_Exports/
    └── Tools/             ← เครื่องมือผู้ขาย (KeyGen.exe)
        ├── KeyGen.exe
        └── _internal/
    ```
  * รวม database.db พร้อมข้อมูลเริ่มต้นไว้ในแพ็คเกจ
* **Build Info:**
  * Platform: Windows 11 (10.0.26200)
  * Python: 3.12.10
  * PyInstaller: 6.20.0
  * StorePOS.exe: ~17 MB
  * KeyGen.exe: ~2.8 MB

---

## [1.0.2] - 2026-07-16

### 🔑 1. เปลี่ยนรหัสผ่านตั้งต้นและสร้างบัญชีผู้ใช้จำกัดสิทธิ์ (Default Credentials & Role Setup)
* **การปรับปรุง:** 
  * เปลี่ยนรหัสผ่านของผู้ดูแลระบบจาก `admin` / `admin` เป็น **`admin`** / **`psoft123`** เพื่อความปลอดภัยในการเปิดโปรแกรมครั้งแรก
  * สร้างบัญชีผู้ใช้ระดับพนักงานขายจำลองขึ้นมาโดยอัตโนมัติ คือ **`user`** / **`user123`** (Role: `cashier`)
  * ปรับสิทธิ์การใช้งานบัญชีพนักงานขาย ให้สามารถเข้าถึงเฉพาะส่วนขายสินค้า (POS) และดูรายการสินค้าเท่านั้น เมนูสต็อก สถิติการเงิน รายงานผู้ใช้ และการตั้งค่า จะเข้าถึงได้เฉพาะบัญชี Admin เท่านั้น
* **ไฟล์ที่แก้ไข:** [database/db_manager.py](file:///c:/Users/admin/Documents/store-pos/database/db_manager.py)

---

### 🖨️ 2. แก้ไขปัญหาตั้งค่าเครื่องพิมพ์ไม่จำค่า (Printer Settings Persistence & GUI Auto-Recommend)
* **ปัญหาที่พบ:** การแอบเขียนทับการตั้งค่าเครื่องพิมพ์ในฐานข้อมูลของระบบเดิมส่งผลให้ค่าที่ผู้ใช้กำหนด (เช่น เปลี่ยนเป็น `thermal`) ถูกบังคับถอยกลับไปเป็น `windows` ทุกครั้งที่มีการติดต่อฐานข้อมูล ทำให้เครื่องจริงไม่สามารถจำค่าได้
* **ไฟล์ที่แก้ไข:** [database/db_manager.py](file:///c:/Users/admin/Documents/store-pos/database/db_manager.py), [ui/settings_window.py](file:///c:/Users/admin/Documents/store-pos/ui/settings_window.py)
* **จุดที่ทำการแก้ไข:**
  * **หลังบ้าน:** เอาตัวตรวจเช็คและบังคับเขียนทับอัตโนมัติออกจากระบบฐานข้อมูล `db_manager.py` ถาวร เพื่อเปิดทางให้ระบบจดจำค่าที่ผู้ใช้เลือกจริงอย่างปลอดภัยร้อยเปอร์เซ็นต์
  * **หน้าบ้าน:** เปลี่ยนจากการตรวจจับ trace ตัวแปรซึ่งไปเขียนทับค่าโหลดเริ่มต้น มาเป็นการใช้ Combobox callback เมื่อผู้ใช้คลิกเลือกเครื่องพิมพ์ตระกูล `"XP-58"` ใน UI ด้วยตนเอง ระบบจะช่วยพรีเซ็ตแนะนำตัวเลือกเป็น `"windows"` และขนาดกระดาษ `"58mm"` ทันที แต่คงสิทธิ์ให้ผู้ใช้สลับและบันทึกโหมด `thermal` ได้อย่างอิสระ
  
---

### 🇹🇭 3. แก้ไขปัญหาพิมพ์ภาษาไทยมั่วในโหมดเครื่องพิมพ์สลิปด่วน (Thermal Printer ESC/POS Thai Code Page Fix)
* **ปัญหาที่พบ:** เมื่อสั่งพิมพ์ผ่านโหมด Thermal Printer (ESC/POS ส่งข้อมูล RAW โดยตรง) อักขระภาษาไทยถูกเรนเดอร์ออกมาเป็นภาษาขยะมั่วซั่ว เนื่องจากตัวเครื่องพิมพ์ Xprinter และเครื่องจีน XP-58/XP-80 ทั่วไปในไทยต้องการรหัสตารางภาษาไทย (Code Page) ลำดับที่ 18 (TIS-620/CP874) แต่ตัวโค้ดเดิมระบุเป็นตารางลำดับที่ 26
* **ไฟล์ที่แก้ไข:** [utils/printer_utils.py](file:///c:/Users/admin/Documents/store-pos/utils/printer_utils.py)
* **จุดที่ทำการแก้ไข:**
  * ปรับเปลี่ยนรหัสคำสั่งสลับตารางอักขระภาษาไทย `ESC t` ในคำสั่ง ESC/POS จากเดิม `\x1a` (Code Page 26) ให้เป็น **`\x12` (Code Page 18 - TIS-620/CP874)** ซึ่งเป็นค่าสากลสำหรับบอร์ดและชิปเซ็ตเครื่องพิมพ์ใบเสร็จความร้อนในประเทศไทย ทำให้การส่งข้อความภาษาไทยผ่านโหมด Thermal พิมพ์ออกมาได้อย่างถูกต้องและไม่เกิดภาษาขยะมั่วซั่วอีกต่อไป

---


---

### 🏷️ 2. ปรับปรุงระบบพิมพ์บาร์โค้ดสินค้า (Bulk Barcode Label PDF Printing Fix)
* **ปัญหาที่พบ:** การสั่งพิมพ์ป้ายบาร์โค้ดสินค้าลงตาราง A4 เดิมพิมพ์ออกมากระดาษว่างเปล่า มีแต่เลขรหัสสินค้าและราคา แต่ไม่มีแถบเส้นบาร์โค้ดที่สามารถยิงสแกนได้จริง เนื่องจากฟังก์ชันใน ReportLab รุ่นที่ใช้ไม่สามารถเรนเดอร์ลายเส้น Code128 ลง PDF แบบ Canvas ได้สมบูรณ์
* **ไฟล์ที่แก้ไข:** [utils/pdf_utils.py](file:///c:/Users/admin/Documents/store-pos/utils/pdf_utils.py)
* **จุดที่ทำการแก้ไข:**
  * เขียนฟังก์ชัน `create_barcode_labels_pdf` ใหม่ทั้งหมด โดยดึงไลบรารี `python-barcode` มาสร้างรูปภาพแถบสแกน (PNG) ขึ้นมาก่อน
  * แปลงรูปภาพบาร์โค้ดที่สร้างเสร็จแล้ว ฝังลงตาราง A4 ด้วย ReportLab `Image` flowable
  * ยืนยันความกว้างและสัดส่วนของเส้นบาร์โค้ดที่ได้มาตรฐานการยิงสแกนของเครื่องยิงบาร์โค้ด (ปืนสแกน) 100%

---

### 📂 3. แก้ไขข้อผิดพลาดกู้คืนข้อมูล (Restore ZIP Directory Path Conflict Fix)
* **ปัญหาที่พบ:** เกิดข้อผิดพลาด `Not a directory` (`Errno 20`) หรือ `PermissionError` ระหว่างการสั่งกู้คืนข้อมูล (Restore ZIP) บนบางระบบปฏิบัติการ เนื่องจากใน ZIP สำรองข้อมูลมักจะมีโฟลเดอร์ซ่อนหรือโฟลเดอร์ขยะของ OS (เช่น `__MACOSX/`) ปะปนอยู่ เมื่อคำสั่งในระบบพยายามคัดลอกโฟลเดอร์เหล่านั้นด้วยคำสั่ง `shutil.copy` ที่ทำมาสำหรับไฟล์จึงส่งผลให้เกิดการแครช
* **ไฟล์ที่แก้ไข:** [ui/settings_window.py](file:///c:/Users/admin/Documents/store-pos/ui/settings_window.py)
* **จุดที่ทำการแก้ไข:**
  * ปรับปรุงลูปการกู้คืนรูปภาพสินค้าและไฟล์ใบเสร็จ PDF ในฟังก์ชัน `restore_database`
  * บังคับใช้คำสั่งตรวจสอบ `is_file()` ก่อนทำการคัดลอกไฟล์ ป้องกันไม่ให้หยิบยกโฟลเดอร์ย่อยใด ๆ ที่ปนมาใน ZIP มาเขียนทับไฟล์ในระบบ

---

### 💾 4. ปรับปรุงความปลอดภัยของฐานข้อมูลในระบบสำรอง (WAL Mode Database Backup Safe Checkpoint)
* **ปัญหาที่พบ:** ระบบการสำรองข้อมูล (Backup ZIP) คัดลอกเฉพาะไฟล์ `database.db` แต่ใน SQLite ที่เปิดโหมด WAL ข้อมูลล่าสุดที่ถูกเขียนมักจะอยู่ในไฟล์แคช `database.db-wal` ส่งผลให้ข้อมูลที่ยังไม่โดนบันทึกลงไฟล์หลักตกหล่นจากการสำรองข้อมูลและเกิดความเสียหาย
* **ไฟล์ที่แก้ไข:** [ui/settings_window.py](file:///c:/Users/admin/Documents/store-pos/ui/settings_window.py)
* **จุดที่ทำการแก้ไข:**
  * เพิ่มคำสั่ง `PRAGMA wal_checkpoint(TRUNCATE)` ในจุดเริ่มเขียนไฟล์ ZIP สำรอง
  * ข้อมูลแคชทั้งหมดจะถูกบังคับให้เคลียร์และรวมไฟล์ลงฐานข้อมูลหลักก่อนทำการบีบอัด รับประกันว่าข้อมูลล่าสุดบน ZIP จะตรงกับสถานะในแอปพลิเคชันจริง

---

### 📦 5. ปรับปรุงการจัดเตรียมโฟลเดอร์โปรแกรมสำเร็จรูป (Psoft Desktop Portable Structure Fix)
* **ปัญหาที่พบ:** ไฟล์ `database.db` และภาพสินค้าที่คัดลอกให้ลูกค้าก่อนหน้านี้อยู่ใน `_internal/data` แต่โครงสร้างแอปพลิเคชันเวอร์ชัน `.exe` จะมองหาที่ตำแหน่ง `data` ชั้นนอกเลเวลเดียวกับตัวโปรแกรมหลัก ส่งผลให้เมื่อรันแอปจะเกิดฐานข้อมูลว่างทับถม
* **จุดที่ปรับปรุง:** ย้ายตำแหน่งไฟล์ในตัวติดตั้ง `Desktop\Psoft` จัดวาง `data/database.db` และ `data/products/` ไว้ที่ชั้นนอกสุด คู่ขนานกับ `StorePOS.exe` เพื่อซิงก์ข้อมูล Dev และตัวจริงลูกค้าได้อย่างลงตัว

---

## [1.0.1] - 2026-07-15

### 🔧 1. แก้ไขปัญหาเครื่องพิมพ์พิมพ์ภาษาไทยมั่ว (GDI Printer Garbled Character Auto-Fix)
* **ปัญหาที่พบ:** เครื่องพิมพ์ซีรีส์ **XP-58** (เช่น `XP-58 (copy 1)`) ทำงานในระบบ GDI ซึ่งต้องการตั้งค่าเป็น `printer_type = 'windows'` และ `paper_size = '58mm'` จึงจะสามารถเรนเดอร์ภาษาไทยได้ถูกต้อง แต่เมื่อผู้ใช้ทำการ **"รีเซ็ตระบบ"** หรือ **"กู้คืนข้อมูล (Restore Zip)"** ค่าในตาราง `settings` จะโดนทับด้วยค่าเริ่มต้น (`printer_type = 'thermal'`, `paper_size = 'A4'`) ทำให้สลีปพิมพ์รหัสคำสั่งดิบออกมาเป็นภาษามั่ว
* **ไฟล์ที่แก้ไข:** [database/db_manager.py](file:///c:/Users/admin/Documents/store-pos/database/db_manager.py)
* **จุดที่ทำการแก้ไข:** 
  * เพิ่มฟังก์ชันการตรวจสอบอัตโนมัติ `_check_and_auto_init(self)` เข้าไปในกระบวนการเชื่อมต่อฐานข้อมูล `connect(self)`
  * ทุกครั้งที่มีการติดต่อฐานข้อมูล ระบบจะคอยเช็คชื่อเครื่องพิมพ์ที่ตั้งค่าไว้ หากมีคำว่า **"XP-58"** ระบบจะทำการตรวจสอบและบังคับตั้งค่าเป็นประเภท **`windows`** และขนาดกระดาษ **`58mm`** ให้โดยอัตโนมัติทันที ป้องกันปัญหามั่วภาษาถาวร

---

### 📥 2. แก้ไขข้อผิดพลาด UNIQUE Constraint ของบาร์โค้ดในการนำเข้า Excel (Excel Import Barcode Conflict Fix)
* **ปัญหาที่พบ:** เมื่อนำเข้าไฟล์ Excel แล้วพบบาร์โค้ดที่มีอยู่แล้วในระบบ (โดยเฉพาะตัวที่ถูกลบไปแล้วหรือซ่อนไว้ ซึ่งมีสถานะ `is_active = 0`) ระบบจะพยายามส่งคำสั่ง `INSERT` ข้อมูลใหม่เข้าตาราง ส่งผลให้ฐานข้อมูลขัดแย้งกับข้อกำหนด UNIQUE ของคอลัมน์บาร์โค้ด และเกิด Error `sqlite3.IntegrityError: UNIQUE constraint failed: products.barcode` ทำให้การนำเข้าล้มเหลว
* **ไฟล์ที่แก้ไข:** [ui/product_window.py](file:///c:/Users/admin/Documents/store-pos/ui/product_window.py)
* **จุดที่ทำการแก้ไข:**
  * ปรับปรุงฟังก์ชัน `import_products_action` ให้ตรวจสอบความซ้ำซ้อนของบาร์โค้ดแบบ Global ทั้งตาราง (ไม่แยกสถานะ `is_active`)
  * หากพบบาร์โค้ดซ้ำที่สถานะปัจจุบันเป็น `is_active = 1` ระบบจะข้ามการนำเข้าตัวนั้น (ตามข้อกำหนดการข้ามสินค้าซ้ำ)
  * หากพบบาร์โค้ดซ้ำที่มีสถานะเป็น `is_active = 0` (สินค้าเก่าที่เคยลบไป) ระบบจะสลับคำสั่งจากการเพิ่มใหม่ (Insert) ไปเป็น **การอัปเดตและคืนชีพสินค้าเดิม (Update & Reactivate to `is_active = 1`)** ทำให้ข้อมูลนำเข้าไหลลื่นโดยไม่แครช

---

### 📊 3. แก้ไขข้อผิดพลาด MergedCell ของการส่งออกรายงานคอลัมน์กว้าง (Excel MergedCell Auto-width Fix)
* **ปัญหาที่พบ:** เกิดข้อผิดพลาด `'MergedCell' object has no attribute 'column_letter'` ระหว่างกระบวนการส่งออกไฟล์ Excel ที่มีคอลัมน์หัวข้อผสานเซลล์ (MergedCell) เนื่องจากฟังก์ชันการปรับความกว้างคอลัมน์อัตโนมัติพยายามดึงข้อมูลตัวอักษรของเซลล์ตรง ๆ
* **ไฟล์ที่แก้ไข:** [utils/excel_utils.py](file:///c:/Users/admin/Documents/store-pos/utils/excel_utils.py)
* **จุดที่ทำการแก้ไข:**
  * ปรับแต่งฟังก์ชันใน `ExcelManager.export_to_excel` ให้ดึงโมดูล `get_column_letter` จาก `openpyxl.utils` มาคำนวณและใช้คำสั่ง `get_column_letter(column[0].column)` ในการหาชื่อคอลัมน์แทน ป้องกันไม่ให้แอปพลิเคชันค้างขณะส่งรายงาน
