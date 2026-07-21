# รายงานสรุปการจัดระเบียบโครงสร้างโฟลเดอร์โปรเจกต์ (Project Directory Organization Report)

รายงานฉบับนี้จัดทำขึ้นเพื่อสรุปผลการปรับปรุง จัดระเบียบ และแยกประเภทไฟล์ในโปรเจกต์ StorePOS ให้มีความเป็นระเบียบเรียบร้อย ตามมาตรฐานการพัฒนาซอฟต์แวร์ระดับสากล

---

## 1. วัตถุประสงค์ของการจัดโครงสร้างใหม่

1. **แยกส่วนประกอบอย่างชัดเจน:** แยกไฟล์ซอร์สโค้ดหลัก (Core App), สคริปต์ทดสอบ (Test Scripts), เครื่องมือแอดมิน (Admin Tools), และเอกสารรายงาน (Documentation) ออกจากกัน
2. **ลดความแออัดในโฟลเดอร์หลัก (Root Directory Clean-up):** ย้ายไฟล์ทดลองและไฟล์ประกอบต่างๆ เข้าโฟลเดอร์เฉพาะ เพื่อให้โฟลเดอร์หลักคงไว้เฉพาะไฟล์สำคัญในการเริ่มทำงานเท่านั้น
3. **รองรับการทดสอบอัตโนมัติ (Automated Testing Support):** รวบรวมสคริปต์ Unit Test และ End-to-End (E2E) ไว้ในโฟลเดอร์ `tests/` เพื่อความสะดวกในการรันสอบทาน

---

## 2. โครงสร้างโฟลเดอร์ที่ปรับปรุงใหม่ (New Directory Structure)

```text
c:/Users/admin/Documents/store-pos/
├── main.py                        # ไฟล์เปิดโปรแกรมหลัก (Production Version)
├── main_trial.py                  # ไฟล์เปิดโปรแกรมทดลองใช้ 15 วัน
├── main_trial_3days.py            # ไฟล์เปิดโปรแกรมทดลองใช้ 3 วัน
├── config.py                      # ไฟล์ตั้งค่าระบบกลาง
├── performance_config.py          # ไฟล์ตั้งค่าโหมดประสิทธิภาพสูง (Low-End Mode)
├── keygen_standalone.py           # สคริปต์เครื่องมือ Admin KeyGen (ทางเข้าหลัก)
├── requirements.txt               # รายการ Python Dependencies
├── README.md                      # คู่มือแนะนำโปรเจกต์ (อัปเดตล่าสุด ไม่มีอิโมจิ)
├── icon.ico                       # ไอคอนโปรแกรม
├── FC Sara Samkan...ttf           # ฟอนต์ภาษาไทยสำหรับใบเสร็จ
│
├── ui/                            # โมดูลหน้าจอผู้ใช้ (CustomTkinter GUI Views)
│   ├── pos_window.py              # หน้าขายสินค้า POS
│   ├── product_window.py          # หน้าจัดการสินค้า
│   ├── help_window.py             # หน้าคู่มือวิธีใช้งาน (16 หัวข้อ)
│   ├── settings_window.py         # หน้าตั้งค่าระบบและ Auto Backup
│   └── activation_window.py       # หน้าลงทะเบียน Activate
│
├── database/                      # โมดูลจัดการฐานข้อมูล SQLite
│   ├── db_manager.py              # Connection Pool & Foreign Keys Enforcement
│   └── data/                      # ที่เก็บไฟล์ฐานข้อมูล database.db
│
├── utils/                         # โมดูลเครื่องมือช่วยและระบบสนับสนุน
│   ├── logger.py                  # ระบบ บันทึก Log ย้อนหลัง 30 วัน & Export Zip
│   ├── license_system.py          # ระบบตรวจสอบสิทธิ์ตาม HWID & Tolerant Matching
│   ├── backup_utils.py            # ระบบสำรองข้อมูลอัตโนมัติ & Pruning
│   ├── tax_invoice.py             # ระบบสร้าง PDF ใบกำกับภาษีเต็มรูปแบบ
│   ├── delivery_note.py           # ระบบสร้าง PDF ใบส่งของ
│   └── printer_utils.py           # ระบบพิมพ์ใบเสร็จความร้อน Silent Print
│
├── docs/                          # เอกสารรายงานของโปรเจกต์ (Documentation)
│   ├── POS_REFAC_REPORT.md        # รายงานสรุปการปรับปรุงระบบและสิทธิ์การใช้งาน
│   ├── ORGANIZATION_REPORT.md     # รายงานฉบับนี้ (สรุปการจัดระเบียบโฟลเดอร์)
│   ├── CHANGELOG.md               # ประวัติการเปลี่ยนแปลงระบบ
│   └── CHANGELOG_NEW.md           # สรุปฟีเจอร์เวอร์ชันล่าสุด
│
├── tests/                         # ชุดสคริปต์ทดสอบระบบและ E2E Tests
│   ├── test_e2e_full_system.py    # สคริปต์ทดสอบ E2E 10 เลเยอร์หลัก (23/23 PASSED)
│   ├── test_refactoring.py        # สคริปต์ทดสอบ DB, สมาชิก และ Auto Backup
│   ├── verify_license_system.py   # สคริปต์ทดสอบระบบสิทธิ์ 39 ชุดทดสอบ
│   └── ...                        # สคริปต์ทดสอบและสอบทานอื่นๆ
│
├── tools/                         # เครื่องมือแอดมินและไฟล์ Build PyInstaller
│   ├── keygen_standalone.py       # เครื่องมือ Admin KeyGen & Reset Activation
│   ├── license_generator.py       # เครื่องมือสร้างคีย์สำหรับผู้ขาย
│   ├── license_manager.py         # เครื่องมือจัดการสิทธิ์สำหรับนักพัฒนา
│   ├── build_exe.spec             # ไฟล์คอนฟิก PyInstaller สำหรับตัวหลัก
│   ├── build_exe_trial_3days.spec # ไฟล์คอนฟิก PyInstaller สำหรับตัวทดลอง 3 วัน
│   └── build_keygen.spec          # ไฟล์คอนฟิก PyInstaller สำหรับ KeyGen
│
├── Logs/                          # โฟลเดอร์เก็บไฟล์ Log บันทึกข้อผิดพลาดรายวัน
├── Backup/                        # โฟลเดอร์เก็บไฟล์สรุปปิดยอดวัน (Daily Closing)
├── Excel_Exports/                 # โฟลเดอร์เก็บไฟล์ส่งออกรายงาน Excel
└── dist/                          # โฟลเดอร์เก็บไฟล์ติดตั้ง/คอมไพล์โปรแกรม
```

---

## 3. รายละเอียดการโยกย้ายไฟล์ (File Relocation Details)

1. **ย้ายเอกสารทั้งหมดไปไว้ที่ `docs/`:**
   - ย้าย `POS_REFAC_REPORT.md` -> `docs/POS_REFAC_REPORT.md`
   - ย้าย `CHANGELOG.md` -> `docs/CHANGELOG.md`
   - ย้าย `CHANGELOG_NEW.md` -> `docs/CHANGELOG_NEW.md`
   - เพิ่ม `docs/ORGANIZATION_REPORT.md`

2. **ย้ายสคริปต์ทดสอบไปไว้ที่ `tests/`:**
   - รวบรวมสคริปต์ในโฟลเดอร์ `scratch/` ทั้งหมด (28 ไฟล์) ย้ายเข้าโฟลเดอร์ `tests/`
   - ลบโฟลเดอร์ชั่วคราว `scratch/` ออกเพื่อความสะอาด

3. **ย้ายเครื่องมือเครื่องจักรและไฟล์ Spec ไปไว้ที่ `tools/`:**
   - ย้าย `license_generator.py`, `license_manager.py`, `package_desktop.py` เข้า `tools/`
   - ย้ายไฟล์ PyInstaller Spec (`build_exe.spec`, `build_exe_trial_3days.spec`, `build_keygen.spec`) เข้า `tools/`
   - สำเนา `keygen_standalone.py` ไว้ใน `tools/keygen_standalone.py`

4. **ย้ายไฟล์ Debug และ Output:**
   - ย้าย `printer_debug.log` เข้าโฟลเดอร์ `Logs/`
   - ย้าย `StorePOS_Portable.zip` เข้าโฟลเดอร์ `dist/`

---

## 4. ผลการตรวจสอบความถูกต้องหลังจัดโครงสร้าง (Post-Organization Verification)

* ได้ทำการรันชุดทดสอบ End-to-End (`python tests/test_e2e_full_system.py`) จากโครงสร้างโฟลเดอร์ใหม่
* **ผลการทดสอบ: ผ่าน 100% (23/23 TESTS PASSED)** ยืนยันว่าการเปลี่ยนโครงสร้างโฟลเดอร์ไม่กระทบกับการทำงานของแอปพลิเคชันและการนำเข้าโมดูล (Import statement) ใดๆ
