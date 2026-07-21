# ระบบจัดการขายหน้าร้าน (Store POS System)

ระบบจัดการจุดขาย (Point of Sale) ที่พัฒนาด้วยภาษา Python และ CustomTkinter ออกแบบมาให้มีความสวยงาม ทันสมัย ใช้งานง่าย แข็งแกร่ง และรองรับการทำงานแบบ Offline เต็มรูปแบบ พร้อมระบบสมาชิก การคำนวณแต้มสะสม การออกใบกำกับภาษี การสำรองข้อมูลอัตโนมัติ และระบบสิทธิ์การใช้งานที่ปลอดภัย

---

## ฟีเจอร์หลักของระบบ (Key Features)

### 1. ระบบขายหน้าร้าน (POS System)
* **Barcode Scanning:** รองรับการยิงสแกนบาร์โค้ดต่อเนื่อง (Auto-focus) เพิ่มสินค้าเข้าตะกร้าได้ทันที พร้อมระบบแปลภาษาไทยเป็นตัวเลขภาษาอังกฤษให้อัตโนมัติ ป้องกันปัญหาสแกนติดภาษาไทย
* **Multi-Session & Hold Bill:** ระบบพักบิลแยกอิสระ สามารถเปิดหน้าขายได้หลายหน้าจอพร้อมกัน [F9]
* **Point Redemption:** ระบบนำแต้มสะสมของสมาชิกมาแลกเป็นส่วนลดเงินสดในตะกร้าสินค้า พร้อมคำนวณภาษี VAT 7% [F8] และระบบซิงค์สองทางป้องกันลูป
* **Quick Checkout:** ชำระเงินด่วน [F10] รองรับการชำระเงินสด เงินโอน พร้อมเพย์ QR Code และแยกประเภทการชำระเงิน
* **Silent Thermal & GDI Printing:** พิมพ์สลิปใบเสร็จแบบเงียบตรงไปยังเครื่องพิมพ์ความร้อน (Thermal Printer 58mm/80mm) ผ่านคำสั่ง ESC/POS และ GDI โดยไม่ต้องเปิดหน้าต่าง PDF
* **Customer Display:** รองรับการเชื่อมต่อจอภาพที่สองฝั่งลูกค้า (Dual Monitor) แสดงรายการสินค้าในตะกร้า ยอดเงินทอน และสไลด์โฆษณาเรียลไทม์

### 2. ระบบจัดการสินค้าและสต็อก (Catalog & Stock Control)
* **Product Wizard:** ตัวช่วยเพิ่มรายการสินค้าใหม่ด่วนทีละขั้นตอน [Ctrl+N]
* **Direct Stock & Movement Audit:** ระบบปรับสต็อกสินค้าโดยตรง และบันทึกประวัติเคลื่อนไหวสต็อก (Audit Trail Log) แยกตามสาเหตุ
* **Barcode Label Printer:** ระบบพิมพ์ป้ายสติ๊กเกอร์บาร์โค้ดสินค้า ออกเครื่องพิมพ์ความร้อน และไฟล์เอกสาร PDF A4
* **Excel Data Import/Export:** รองรับการนำเข้าและส่งออกข้อมูลสินค้าปริมาณมากผ่านไฟล์ Excel (.xlsx)

### 3. ระบบสมาชิกและแต้มสะสม (Member & Loyalty Points)
* **Member Registration:** ระบบลงทะเบียนและจัดการข้อมูลสมาชิก
* **Points Calculation:** ระบบคำนวณแต้มสะสมจากยอดซื้อสินค้าอัตโนมัติ (POINT_EARN_RATE)
* **Point Discount Value:** ระบบแลกแต้มเป็นส่วนลดเงินสด (POINT_REDEEM_VALUE) พร้อมการปรับปรุงยอดแต้มคงเหลือแบบเรียลไทม์

### 4. ระบบเอกสารและการคืนสินค้า (Documents & After-Sales)
* **Void Sale & Auto Restock:** ระบบสืบค้นและทำบิลโมฆะยกเลิกรายการขาย โดยระบบจะนำสินค้าคืนเข้าคลังสต็อกให้อัตโนมัติ
* **Itemized Return:** ระบบรับคืนสินค้าแยกตามรายการ คืนเงินลูกค้า และคืนสต็อก
* **Full Tax Invoice PDF:** ออกเอกสารใบกำกับภาษีเต็มรูปแบบ e-Tax Invoice เป็นไฟล์ PDF
* **Delivery Note PDF:** ออกเอกสารใบส่งของ / ใบแจ้งหนี้เป็นไฟล์ PDF

### 5. ระบบสำรองข้อมูลและจัดการสิทธิ์ (Backup & Licensing)
* **Auto Background Backup:** ระบบสำรองข้อมูลอัตโนมัติทำงานในเบื้องหลัง พร้อมการลบไฟล์สำรองเก่าส่วนเกิน (Pruning) ตามจำนวนที่ตั้งค่าไว้
* **Standard Hardware ID Licensing:** ระบบตรวจสอบสิทธิ์ผูกรหัสคอมพิวเตอร์ (HWID) พร้อมระบบ Tolerant Matching และการตรวจสอบเวลาเครื่องป้องกันการโกงเวลา
* **Date-Based Expiration:** การคำนวณวันหมดอายุตามปฏิทินจริง ไม่บล็อกการใช้งานในวันสุดท้ายก่อนครบกำหนด
* **Admin Maintenance Tool:** เครื่องมือแอดมิน (keygen_standalone.py) สำหรับสร้างรหัส ถอนสิทธิ์ และล้างความจำเครื่อง (Reset Activation & DB Cache)

### 6. ระบบบันทึก Log และวิเคราะห์ปัญหา (Logging & Diagnostic)
* **Global Exception Hooks:** บันทึกข้อผิดพลาดจาก Python Script หลัก, GUI Callbacks (Tkinter report_callback_exception) และ Background Threads (threading.excepthook) ลงในไฟล์ Logs/YYYY-MM-DD.log พร้อม Traceback และเลขบรรทัดครบถ้วน 100%
* **Environment Header:** บันทึกข้อมูล OS Platform, Python Version, และ Path โปรแกรมทุกครั้งเมื่อเริ่มระบบ
* **Export Logs Zip:** ฟังก์ชันบีบอัดไฟล์ Log ทั้งหมดใส่ไฟล์ ZIP เพื่อส่งให้ทีมซัพพอร์ตวิเคราะห์ปัญหาได้อย่างรวดเร็ว

---

## โครงสร้างโฟลเดอร์ของโปรเจกต์ (Project Directory Structure)

```text
store-pos/
├── main.py                        # ไฟล์รันโปรแกรมหลัก (Production Version)
├── main_trial.py                  # ไฟล์รันโปรแกรมทดลองใช้ 15 วัน
├── main_trial_3days.py            # ไฟล์รันโปรแกรมทดลองใช้ 3 วัน
├── config.py                      # ไฟล์ตั้งค่าระบบกลาง
├── performance_config.py          # ไฟล์ตั้งค่าโหมดประสิทธิภาพสูง (Low-End Mode)
├── keygen_standalone.py           # เครื่องมือ Admin KeyGen & Reset Activation
├── requirements.txt               # รายการ Python Dependencies
├── README.md                      # เอกสารแนะนำโปรเจกต์
├── icon.ico                       # ไอคอนโปรแกรม
├── FC Sara Samkan...ttf           # ฟอนต์ภาษาไทยสำหรับใบเสร็จ
│
├── ui/                            # โมดูลหน้าจอผู้ใช้ CustomTkinter (POS, Products, Help, Settings)
├── database/                      # โมดูลจัดการฐานข้อมูล SQLite & Connection Pool
├── utils/                         # โมดูลเครื่องมือช่วย (Logger, License, Backup, Tax Invoice, Printer)
├── docs/                          # เอกสารรายงานของโปรเจกต์ (POS_REFAC_REPORT, ORGANIZATION_REPORT, CHANGELOG)
├── tests/                         # ชุดสคริปต์ทดสอบระบบและ End-to-End Tests (test_e2e_full_system.py)
├── tools/                         # เครื่องมือแอดมินและไฟล์คอนฟิก PyInstaller Spec
├── Logs/                          # โฟลเดอร์เก็บบันทึก Log ข้อผิดพลาดรายวัน
├── Backup/                        # โฟลเดอร์เก็บไฟล์สรุปปิดยอดขายประจำวัน
├── Excel_Exports/                 # โฟลเดอร์เก็บไฟล์รายงานส่งออก Excel
└── dist/                          # โฟลเดอร์เก็บไฟล์คอมไพล์โปรแกรม
```

---

## การเริ่มใช้งานและการรันโปรแกรม (Usage & Setup)

### 1. สภาพแวดล้อมที่จำเป็น (Environment)
* **Python Version:** 3.10 ขึ้นไป (รองรับ Python 3.12)
* **Dependencies Setup:** `pip install -r requirements.txt`

### 2. คำสั่งรันโปรแกรม (Execution Commands)
* **รันโปรแกรมตัวหลัก:**
  ```bash
  python main.py
  ```
* **รันเครื่องมือผู้ขาย Admin KeyGen:**
  ```bash
  python keygen_standalone.py
  ```
* **รันการทดสอบระบบแบบ End-to-End:**
  ```bash
  python tests/test_e2e_full_system.py
  ```

---

## ปุ่มลัดคีย์บอร์ด (Keyboard Shortcuts)

### หน้าขายสินค้า (POS Window)
* **[F1]** : โฟกัสช่องสแกนบาร์โค้ดด่วน (ล้างข้อความเดิมอัตโนมัติ)
* **[F8]** : เปิด/ปิด คำนวณภาษี VAT 7%
* **[F9]** : เปิดหน้าขายใหม่ (Multi-Session / พักบิล)
* **[F10]** หรือ **[Enter]** : เปิดหน้าชำระเงินด่วน
* **[F11]** : ล้างรายการสินค้าทั้งหมดในตะกร้าปัจจุบัน

### หน้าจัดการสินค้า (Products Window)
* **[Ctrl+N]** หรือ **[F5]** : เปิด Wizard เพิ่มสินค้าใหม่ด่วน
* **[Ctrl+F]** : โฟกัสช่องค้นหาสินค้า
* **[Ctrl+R]** : รีเฟรชข้อมูลในตารางสินค้า

---

## การคอมไพล์โปรแกรม (.exe Build)

หากต้องการคอมไพล์โปรแกรมเป็นไฟล์ Executable (.exe) ผ่าน PyInstaller:

1. **คอมไพล์โปรแกรมตัวหลัก:**
   ```bash
   pyinstaller tools/build_exe.spec --clean --noconfirm
   ```
2. **คอมไพล์เครื่องมือ Admin KeyGen:**
   ```bash
   pyinstaller tools/build_keygen.spec --clean --noconfirm
   ```
3. ไฟล์ผลลัพธ์จะถูกจัดเก็บไว้ในโฟลเดอร์ `dist/`

---

*พัฒนาร่วมกับ Antigravity AI*
