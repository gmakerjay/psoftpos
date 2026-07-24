# Progress Log — Store POS Responsive UI & Fixes
Last updated: 2026-07-24

## เป้าหมายของงานนี้
1. ปรับปรุงส่วนติดต่อผู้ใช้ (GUI) ของระบบ Store POS ให้เป็นแบบ Full Responsive สำหรับจอคอมพิวเตอร์ความละเอียดต่ำ/รุ่นเก่า (1300x700 / 1366x768 / 1280x720 ฯลฯ)
2. แก้ไขกระบวนการ Activate ให้ปิดหน้าต่าง Activation และเปลี่ยนไปหน้า Login ทันทีเมื่อผ่าน
3. ปรับปรุงเครื่องมือ KeyGen Tools และส่วนการจัดการ License ให้สามารถกำหนดจำนวนวันได้ตามใจคนขาย และสามารถรีเซ็ตสิทธิ์คืนค่ากลับสู่หน้า Activate ได้จริงอย่างราบรื่น
4. แก้ไขบั๊ก Splash Screen ค้างที่ 54% หลังสั่งรีเซ็ตระบบและรีสตาร์ทเครื่อง
5. แก้ไขบั๊ก pop up Error 22 (invalid argument) เมื่อทำการกู้คืนข้อมูล (Restore ZIP) หรือนำเข้าข้อมูล

## สถานะปัจจุบัน
ดำเนินการแก้ไขและทดสอบระบบทั้งหมดสำเร็จสมบูรณ์ 100% (ทุก Automated Test ผ่าน 100%)

## ข้อเท็จจริงที่ตรวจสอบแล้ว (verified facts)
- **บั๊ก Splash Screen ค้าง 54%**:
  - **สาเหตุ**: เกิดจาก Thread Deadlock ใน `DatabaseManager` เมื่อสั่งรีเซ็ตระบบและลบไฟล์ DB ทิ้ง พอแอปรีสตาร์ท Background Thread ใน Splash Screen (Task 3 ที่ 54%) เรียก `LicenseManager.check_activation()` ➔ `verify_system_clock()` ➔ `db.connect()` ➔ `_check_and_auto_init()` ➔ `initialize_database()` ➔ `connect()` ซึ่งพยายาม Re-lock `_pool_lock` ที่เป็น `threading.Lock()` (ไม่ใช่ Reentrant) ทำให้เกิด Deadlock ค้างถาวร
  - **การแก้ไข**: เปลี่ยน `_pool_lock` เป็น **`threading.RLock()`** และปรับ `initialize_database()` ให้คง Active Connection สำหรับ Caller
- **บั๊ก Error 22 (invalid argument) ในการกู้คืน/นำเข้าข้อมูล**:
  - **สาเหตุ**: การแตกไฟล์ ZIP โดยไม่กรองไฟล์ขยะของ OS (เช่น `__MACOSX`) และการพยายามคัดลอกเขียนทับไฟล์ฐานข้อมูลในขณะที่ Connection หรือไฟล์ WAL/SHM ยังเปิดค้างอยู่บนระบบปฏิบัติการ Windows
  - **การแก้ไข**: ใช้ Safe ZIP Extraction กรองไฟล์ขยะของ OS, เรียก `DatabaseManager.close_all_connections()` และ `gc.collect()` เพื่อเคลียร์ Handle บน Windows 100% ก่อนย้ายไฟล์ด้วย `shutil.copy2`

## เอกสารสรุปงานและคู่มือการตามบั๊กรายละเอียด
- อ่านเอกสารฉบับเต็มได้ที่: [docs/RESPONSIVE_AND_LICENSE_SYSTEM_DOCS.md](file:///c:/Users/admin/Documents/store-pos/docs/RESPONSIVE_AND_LICENSE_SYSTEM_DOCS.md)

## เสร็จแล้ว (ประวัติ — ห้ามลบ ให้ย้ายมาไว้ตรงนี้แทน)
- [x] ปรับปรุง Responsive UI บนจอคอมรุ่นเก่า/จอเล็ก (F10 ตรึงล่าง ยืดหยุ่นได้ 100%)
- [x] แก้ไขกระบวนการกด Activate ให้ปิดหน้าต่าง Activation และเปลี่ยนไปหน้า Login ทันที
- [x] เพิ่มปุ่ม Custom Expiry Days และ Reset & Launch Activation ใน KeyGen Tools และ POS Settings
- [x] แก้ไขการสแกนตำแหน่งไฟล์สิทธิ์ของ KeyGen ให้เข้าถึงโฟลเดอร์เพื่อนบ้านได้สมบูรณ์
- [x] แก้ไข Process ค้างและปลดล็อกการลบโฟลเดอร์ `_internal` โดยไม่ต้องรีสตาร์ทเครื่องด้วย `os._exit(0)`
- [x] บิวด์โปรแกรมเวอร์ชันล่าสุดส่งมอบไว้ที่ `C:\Users\admin\Desktop\StorePOS_v1.0.0` เรียบร้อย
- [x] แก้ไขบั๊ก Splash Screen ค้างที่ 54% ด้วย `threading.RLock()` และปรับปรุง Auto-init logic
- [x] แก้ไขบั๊ก Error 22 (invalid argument) ในการกู้คืน/นำเข้าข้อมูลด้วย Safe ZIP Extraction และ Handle Cleanup
- [x] เพิ่มรายการสินค้า 100 รายการพร้อมผูกรูปภาพสินค้า และสร้างประวัติการขาย/คืน/สต็อก/สมาชิก 100% สำหรับการทดสอบ Backup & Restore
- [x] ปรับฟอนต์ข้อความหัวคอลัมน์ใบกำกับภาษี (Tax Invoice / A4 Receipt) ให้เป็นสีขาวสว่างสดใสบนพื้นหลังสีน้ำเงิน
- [x] เพิ่มการรองรับการขายสินค้าจำนวนมากแบบ Multi-page Auto-flow พร้อมตรึงหัวตารางทุกหน้า (`repeatRows=1`) และเพิ่มช่องระบุหมายเหตุ
- [x] คอมไพล์โปรแกรม (PyInstaller) และจัดส่งแพ็คเกจพร้อมใช้งานพร้อมข้อมูล 100 รายการไปยัง `C:\Users\admin\Desktop\StorePOS_v1.0.0` เรียบร้อยแล้ว

