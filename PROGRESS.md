# Progress Log — Store POS Responsive UI & Fixes
Last updated: 2026-07-24

## เป้าหมายของงานนี้
1. ปรับปรุงส่วนติดต่อผู้ใช้ (GUI) ของระบบ Store POS ให้เป็นแบบ Full Responsive สำหรับจอคอมพิวเตอร์ความละเอียดต่ำ/รุ่นเก่า (1300x700 / 1366x768 / 1280x720 ฯลฯ)
2. แก้ไขกระบวนการ Activate ให้ปิดหน้าต่าง Activation และเปลี่ยนไปหน้า Login ทันทีเมื่อผ่าน
3. ปรับปรุงเครื่องมือ KeyGen Tools และส่วนการจัดการ License ให้สามารถกำหนดจำนวนวันได้ตามใจคนขาย และสามารถรีเซ็ตสิทธิ์คืนค่ากลับสู่หน้า Activate ได้จริงอย่างราบรื่น
4. แก้ไขบั๊ก Splash Screen ค้างที่ 54% หลังสั่งรีเซ็ตระบบและรีสตาร์ทเครื่อง
5. แก้ไขบั๊ก pop up Error 22 (invalid argument) เมื่อทำการกู้คืนข้อมูล (Restore ZIP) หรือนำเข้าข้อมูล
6. แก้ไขปัญหาเครื่องพิมพ์สลิปตัดกระดาษไวเกินไป/ตัดโดนข้อความท้ายบิลและ QR Code (เช่น SENOR GTP-180, Xprinter, Epson) โดยคงระบบภาษาไทยและการแสดงผลไว้ 100% ไม่แตะต้องระบบภาษา

## สถานะปัจจุบัน
ดำเนินการแก้ไข ทดสอบการพิมพ์จริงกับเครื่องพิมพ์ SENOR GTP-180 และจัดส่งแพ็คเกจเวอร์ชัน 1.0.0 สมบูรณ์ 100% (ทุก Automated & Hardware Test ผ่าน 100%)

## ข้อเท็จจริงที่ตรวจสอบแล้ว (verified facts)
- **การทดสอบพิมพ์จริงบนเครื่องพิมพ์ SENOR GTP-180 & Thermal Printers (ผ่าน 100%)**:
  - **การเพิ่มราคาต่อหน่วยในใบเสร็จ**: แก้ไขฟังก์ชัน `_render_receipt_image` ให้ใส่ราคาต่อหน่วยและจำนวนสินค้า (`qty x unit_price` ➔ `total_price`) แสดงผล 2 บรรทัดมาตรฐานแบบ POS สากล
  - **การแก้ปัญหา QR Code โดนตัดครึ่งรูป**: คำนวณความสูง `img_h` รวมเข้าผืนผ้าใบ Bitmap Canvas เต็มรูป 100% (987px) ไม่โดนตัดขอบอีกต่อไป
  - **การแก้ปัญหากระดาษตัดชิดเกินไป**: เพิ่มระยะขอบล่าง 100px และส่งคำสั่ง `ESC d 8` (Feed 8 lines) ก่อนสั่ง `GS V \x42 \x00` ดันกระดาษพ้นใบมีดตัด 100%
- **การปฏิบัติตาม Dev Discipline & Release Rules (skills.md)**:
  - กำหนดเวอร์ชันคงที่ **`1.0.0`** เสมอ
  - จัดตั้งโฟลเดอร์ปลายทางบน Desktop ทั้ง [StorePOS_v1.0.0](file:///C:/Users/admin/Desktop/StorePOS_v1.0.0) และ [STDeploy](file:///C:/Users/admin/Desktop/STDeploy)
  - คอมไพล์เฉพาะตัวโปรแกรมหลัก (`StorePOS_Full`) และเครื่องมือ KeyGen (`Tools/KeyGen.exe`)
- **ผลการทดสอบ Database Stress Test (26/26 Passed)**:
  - รันการทดสอบผ่าน [tests/test_db_stress.py](file:///c:/Users/admin/Documents/store-pos/tests/test_db_stress.py) ครอบคลุม Integrity, Scalability (500/1000 สินค้า), Backup/Restore, Concurrent R/W (310 ops), Transaction Rollback, และยอดขาย 200 บิล/วัน ผลลัพธ์ผ่าน 100%
  - บันทึกรายงานสรุปฉบับเต็มไว้ที่ [docs/DATABASE_STRESS_TEST_REPORT.md](file:///c:/Users/admin/Documents/store-pos/docs/DATABASE_STRESS_TEST_REPORT.md)
- **ผลการทดสอบ Daily Shift Close & Backup (100% Passed)**:
  - รันการทดสอบผ่าน [tests/test_daily_close_backup.py](file:///c:/Users/admin/Documents/store-pos/tests/test_daily_close_backup.py) ยืนยันว่าการกดปิดยอดวันด้วยตนเอง จะสร้างไฟล์ Excel (`.xlsx`) และ Text Log (`.txt`) ในโฟลเดอร์ `Backup/` และสืบค้นย้อนหลังได้ตลอดเวลา
- **การคลีนอัพและเตรียมข้อมูลสินค้า 100 รายการ**:
  - รันสคริปต์ [tools/clean_and_populate_100.py](file:///c:/Users/admin/Documents/store-pos/tools/clean_and_populate_100.py) ล้างยอดขายเดิมเป็น 0 ทั้งหมด และเพิ่มสินค้าใหม่ 100 รายการพร้อมผูกรูปภาพสินค้าเรียบร้อย

## เอกสารสรุปงานและคู่มือรายละเอียด
- เอกสารคู่มือระบบ License & Responsive: [docs/RESPONSIVE_AND_LICENSE_SYSTEM_DOCS.md](file:///c:/Users/admin/Documents/store-pos/docs/RESPONSIVE_AND_LICENSE_SYSTEM_DOCS.md)
- รายงานผล Database Stress Test: [docs/DATABASE_STRESS_TEST_REPORT.md](file:///c:/Users/admin/Documents/store-pos/docs/DATABASE_STRESS_TEST_REPORT.md)

## เสร็จแล้ว (ประวัติ — ห้ามลบ ให้ย้ายมาไว้ตรงนี้แทน)
- [x] ทดสอบการพิมพ์จริงกับเครื่องพิมพ์ SENOR GTP-180 ผ่าน 100% (แสดงผลภาษาไทยชัดเจน, แสดงราคาต่อหน่วย, QR Code เต็มรูป, เลื่อนพ้นใบมีดตัด 8 บรรทัด)
- [x] แก้ไขราคาต่อหน่วยและจำนวนสินค้า (`qty x unit_price`) ในใบเสร็จรับเงินให้แสดงผลครบถ้วน
- [x] แก้ไขการคำนวณความสูง Canvas รูป QR Code ไม่ให้ถูกตัดครึ่งรูป
- [x] เพิ่มระยะขอบล่าง 100px และระยะเลื่อนกระดาษ `ESC d 8` ให้พ้นใบมีดตัด 100%
- [x] เพิ่มการตั้งค่าระยะส่งกระดาษก่อนตัด (`printer_feed_lines`) ใน `printer_utils.py` และ `settings_window.py` รองรับ SENOR GTP-180 และเครื่องพิมพ์ทุกรุ่น
- [x] รัน Database Stress Test (26/26 Passed) และจัดทำรายงานลงโฟลเดอร์ Docs
- [x] ทดสอบระบบปิดยอดวัน (Shift Close & Backup Retrieval Test) ผ่าน 100%
- [x] ล้างข้อมูลธุรกรรมเดิมเป็น 0 และเพิ่มสินค้า 100 รายการพร้อมผูกรูปภาพสินค้าเรียบร้อย
- [x] คอมไพล์และจัดส่งแพ็คเกจสมบูรณ์ล่าสุดไปยัง `C:\Users\admin\Desktop\StorePOS_v1.0.0` และ `C:\Users\admin\Desktop\STDeploy`
