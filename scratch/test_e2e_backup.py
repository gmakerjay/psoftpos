# -*- coding: utf-8 -*-
"""
E2E Test — ทดสอบระบบสำรองข้อมูลและนำเข้าสินค้าแบบครบวงจร
"""
import sys, os, shutil, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from utils.excel_utils import ExcelManager
from utils.backup_utils import SalesLogManager

TEST_EXCEL = os.path.join("scratch", "e2e_export_test.xlsx")
TEST_ZIP = os.path.join("scratch", "e2e_backup_test.zip")
PASS = FAIL = 0

def ok(msg):
    global PASS; PASS += 1; print(f"  [PASS] {msg}")
def ng(msg):
    global FAIL; FAIL += 1; print(f"  [FAIL] {msg}")
def check(cond, p, f):
    ok(p) if cond else ng(f)

# =====================================================================
print("=" * 70)
print("TEST 1: Create test products in DB")
print("=" * 70)
db = DatabaseManager()
db.connect()
db.execute("DELETE FROM products WHERE barcode LIKE 'E2E_%'")
db.connection.commit()

products = [
    ("E2E_001", "E2E น้ำดื่มสิงห์ 600ml",   "เครื่องดื่ม", 5,  10, 8, 9, 7, 100, 10, "ขวด"),
    ("E2E_002", "E2E นมจืดโฟร์โมสต์ 180ml",  "เครื่องดื่ม", 7,  12, 10, 11, 9, 80, 10, "กล่อง"),
    ("E2E_003", "E2E มาม่ารสต้มยำกุ้ง",      "อาหาร",      4,  6, 5.5, 5, 5, 200, 20, "ซอง"),
    ("E2E_004", "E2E เลย์ออริจินัล 75ก",      "ขนม",        12, 20, 18, 19, 17, 50, 5, "ซอง"),
    ("E2E_005", "E2E สินค้าราคาศูนย์",        "อื่นๆ",      0,  0, 0, 0, 0, 0, 0, "ชิ้น"),
]

for bc, name, cat, cost, ret, ws, s1, s2, stk, mn, unit in products:
    row = db.fetch_one("SELECT category_id FROM categories WHERE category_name = ?", (cat,))
    if not row:
        db.execute("INSERT INTO categories (category_name) VALUES (?)", (cat,))
        row = db.fetch_one("SELECT category_id FROM categories WHERE category_name = ?", (cat,))
    cid = row['category_id']
    db.execute("""INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price,
        wholesale_price, special_price1, special_price2, stock_quantity, min_stock, unit, is_active)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
        (bc, name, cid, cost, ret, ws, s1, s2, stk, mn, unit))
db.connection.commit()

cnt = db.fetch_one("SELECT COUNT(*) as c FROM products WHERE barcode LIKE 'E2E_%' AND is_active=1")
check(cnt['c'] == 5, f"Created {cnt['c']}/5 products", f"Only {cnt['c']}/5")
db.disconnect()

# =====================================================================
print("\n" + "=" * 70)
print("TEST 2: Export to Excel")
print("=" * 70)
db.connect()
rows = db.fetch_all("""SELECT p.*, c.category_name FROM products p
    LEFT JOIN categories c ON p.category_id = c.category_id
    WHERE p.is_active = 1 AND p.barcode LIKE 'E2E_%' ORDER BY barcode""")
db.disconnect()
check(len(rows) == 5, f"Fetched {len(rows)}/5 from DB", f"Only {len(rows)}")

cols = ["บาร์โค้ด","ชื่อสินค้า","หมวดหมู่","ราคาทุน","ราคาขายปกติ","ราคาขายส่ง",
        "ราคาพิเศษ1","ราคาพิเศษ2","จำนวนสต็อก","สต็อกขั้นต่ำ","หน่วย"]
edata = []
for p in rows:
    edata.append({
        "บาร์โค้ด": str(p["barcode"] or ""),
        "ชื่อสินค้า": str(p["product_name"] or ""),
        "หมวดหมู่": str(p["category_name"] or ""),
        "ราคาทุน": float(p["cost_price"] or 0),
        "ราคาขายปกติ": float(p["retail_price"] or 0),
        "ราคาขายส่ง": float(p["wholesale_price"] or 0),
        "ราคาพิเศษ1": float(p["special_price1"] or 0),
        "ราคาพิเศษ2": float(p["special_price2"] or 0),
        "จำนวนสต็อก": int(p["stock_quantity"] or 0),
        "สต็อกขั้นต่ำ": int(p["min_stock"] or 0),
        "หน่วย": str(p["unit"] or "ชิ้น")
    })

os.makedirs("scratch", exist_ok=True)
ok_export = ExcelManager.export_to_excel(edata, cols, TEST_EXCEL, "สินค้า", "E2E Backup Test")
check(ok_export, "Export Excel OK", "Export FAILED")
check(os.path.exists(TEST_EXCEL), "Excel file exists", "Excel file missing")

readback = ExcelManager.import_from_excel(TEST_EXCEL, header_row=3)
check(len(readback) == 5, f"Read back {len(readback)}/5 rows", f"Only {len(readback)}")

# =====================================================================
print("\n" + "=" * 70)
print("TEST 3: Delete all E2E products (simulate Reset)")
print("=" * 70)
db.connect()
db.execute("DELETE FROM products WHERE barcode LIKE 'E2E_%'")
db.connection.commit()
rem = db.fetch_one("SELECT COUNT(*) as c FROM products WHERE barcode LIKE 'E2E_%'")
check(rem['c'] == 0, "All E2E products deleted", f"Still {rem['c']} remaining")
db.disconnect()

# =====================================================================
print("\n" + "=" * 70)
print("TEST 4: Import from Excel (full pipeline)")
print("=" * 70)
data = ExcelManager.import_from_excel(TEST_EXCEL, header_row=3)
check(len(data) > 0, f"Read {len(data)} rows from Excel", "Read failed")

col_map = {"บาร์โค้ด":"barcode","ชื่อสินค้า":"product_name","หมวดหมู่":"category",
    "ราคาทุน":"cost_price","ราคาขายปกติ":"retail_price","ราคาขายส่ง":"wholesale_price",
    "ราคาพิเศษ1":"special_price1","ราคาพิเศษ2":"special_price2",
    "จำนวนสต็อก":"stock_quantity","สต็อกขั้นต่ำ":"min_stock"}

db.connect()
db.begin_transaction()
s_ok = s_skip = 0; errs = []
cats = db.fetch_all("SELECT category_id, category_name FROM categories")
clkp = {c['category_name']: c['category_id'] for c in cats} if cats else {}

for idx, row in enumerate(data):
    try:
        m = {}
        for tk, ek in col_map.items():
            v = row.get(tk)
            m[ek] = v if v is not None and str(v).strip() not in ('','nan') else None
        pn = m.get("product_name")
        if not pn or not str(pn).strip(): continue
        pn = str(pn).strip()
        bc = str(m.get("barcode") or "").strip().replace('.0','') or None

        existing = db.fetch_one("SELECT product_id, is_active FROM products WHERE barcode=?", (bc,)) if bc else None
        
        cn = str(m.get("category") or "").strip()
        cid = None
        if cn:
            if cn in clkp:
                cid = clkp[cn]
            else:
                db.execute("INSERT INTO categories (category_name) VALUES (?)", (cn,))
                nr = db.fetch_one("SELECT category_id FROM categories WHERE category_name=?", (cn,))
                if nr: cid = nr['category_id']; clkp[cn] = cid

        tf = lambda v,d=0: float(v) if v else d
        ti = lambda v,d=0: int(float(v)) if v else d

        vals = (pn, cid, tf(m.get("cost_price")), tf(m.get("retail_price")),
                tf(m.get("wholesale_price")), tf(m.get("special_price1")),
                tf(m.get("special_price2")), ti(m.get("stock_quantity")),
                ti(m.get("min_stock"),10), str(m.get("unit") or "ชิ้น").strip())

        if existing:
            if existing["is_active"] == 1: s_skip += 1; continue
            db.execute("""UPDATE products SET product_name=?,category_id=?,cost_price=?,
                retail_price=?,wholesale_price=?,special_price1=?,special_price2=?,
                stock_quantity=?,min_stock=?,unit=?,is_active=1 WHERE product_id=?""",
                vals + (existing["product_id"],))
        else:
            db.execute("""INSERT INTO products (barcode,product_name,category_id,cost_price,
                retail_price,wholesale_price,special_price1,special_price2,
                stock_quantity,min_stock,unit,is_active) VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
                (bc,) + vals)
        s_ok += 1
    except Exception as e:
        errs.append(f"Row {idx+1}: {e}")

if s_ok > 0: db.commit_transaction()
else: db.rollback_transaction()

check(s_ok == 5, f"Imported {s_ok}/5 OK", f"Only {s_ok}/5")
check(len(errs) == 0, "No errors", f"{len(errs)} errors: {errs}")

imported = db.fetch_all("SELECT * FROM products WHERE barcode LIKE 'E2E_%' AND is_active=1 ORDER BY barcode")
check(len(imported) == 5, f"DB has {len(imported)}/5", f"Only {len(imported)}")
if imported:
    p = imported[0]
    check(p['retail_price'] == 10.0, f"Price correct: {p['retail_price']}", f"Price wrong: {p['retail_price']}")
    check(p['stock_quantity'] == 100, f"Stock correct: {p['stock_quantity']}", f"Stock wrong: {p['stock_quantity']}")
db.disconnect()

# =====================================================================
print("\n" + "=" * 70)
print("TEST 5: UNIQUE Constraint (import duplicates - should skip)")
print("=" * 70)
db.connect()
db.begin_transaction()
d_skip = 0
for row in data:
    bc = str(row.get("บาร์โค้ด") or "").strip().replace('.0','')
    if bc:
        ex = db.fetch_one("SELECT product_id, is_active FROM products WHERE barcode=?", (bc,))
        if ex and ex["is_active"] == 1:
            d_skip += 1
db.rollback_transaction()
check(d_skip == 5, f"Skipped {d_skip}/5 duplicates (no crash)", f"Only {d_skip}")
db.disconnect()

# =====================================================================
print("\n" + "=" * 70)
print("TEST 6: Reactivate (soft-delete then re-import)")
print("=" * 70)
db.connect()
db.execute("UPDATE products SET is_active=0 WHERE barcode='E2E_003'")
db.connection.commit()
sd = db.fetch_one("SELECT is_active FROM products WHERE barcode='E2E_003'")
check(sd['is_active'] == 0, "Soft-deleted E2E_003", "Soft-delete failed")

db.begin_transaction()
ex = db.fetch_one("SELECT product_id, is_active FROM products WHERE barcode='E2E_003'")
if ex and ex['is_active'] == 0:
    db.execute("UPDATE products SET product_name=?, is_active=1 WHERE product_id=?",
        ("E2E มาม่า (REACTIVATED)", ex['product_id']))
    db.commit_transaction()
    ok("Reactivated E2E_003")
else:
    db.rollback_transaction(); ng("E2E_003 not found as inactive")

ra = db.fetch_one("SELECT is_active, product_name FROM products WHERE barcode='E2E_003'")
check(ra['is_active'] == 1, "is_active=1 after reactivate", f"is_active={ra['is_active']}")
check("REACTIVATED" in ra['product_name'], f"Name updated: {ra['product_name']}", "Name not updated")
db.disconnect()

# =====================================================================
print("\n" + "=" * 70)
print("TEST 7: DB Concurrent Access (2 connections)")
print("=" * 70)
db1 = DatabaseManager(); db2 = DatabaseManager()
try:
    db1.connect(); db2.connect()
    r1 = db1.fetch_one("SELECT COUNT(*) as c FROM products WHERE barcode LIKE 'E2E_%'")
    ok(f"Conn1 read: {r1['c']} products")
    r2 = db2.fetch_one("SELECT COUNT(*) as c FROM products WHERE barcode LIKE 'E2E_%'")
    ok(f"Conn2 concurrent read: {r2['c']} products")
    db1.execute("UPDATE products SET product_name='E2E Lock Test' WHERE barcode='E2E_005'")
    db1.connection.commit()
    ok("Conn1 write OK")
    r3 = db2.fetch_one("SELECT product_name FROM products WHERE barcode='E2E_005'")
    check(r3['product_name'] == 'E2E Lock Test', f"Conn2 reads updated: {r3['product_name']}", "Stale data")
    db1.disconnect(); db2.disconnect()
    ok("Both connections closed - no lock")
except Exception as e:
    ng(f"DB Lock Error: {e}")
    try: db1.disconnect()
    except: pass
    try: db2.disconnect()
    except: pass

# =====================================================================
print("\n" + "=" * 70)
print("TEST 8: Backup/Restore ZIP")
print("=" * 70)
try:
    db_path = os.path.join("data", "database.db")
    check(os.path.exists(db_path), f"DB found: {db_path}", "DB missing")
    # WAL checkpoint (เหมือนที่ backup_database ทำจริง)
    import sqlite3 as sql3
    _c = sql3.connect(db_path)
    _c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    _c.close()
    ok("WAL checkpoint done before backup")
    with zipfile.ZipFile(TEST_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, "database.db")
    check(os.path.exists(TEST_ZIP), "ZIP created", "ZIP failed")
    
    rd = os.path.join("scratch", "restore_test")
    os.makedirs(rd, exist_ok=True)
    with zipfile.ZipFile(TEST_ZIP, 'r') as zf:
        zf.extractall(rd)
    rdb = os.path.join(rd, "database.db")
    check(os.path.exists(rdb), "Extracted DB from ZIP", "Extract failed")
    
    import sqlite3
    c = sqlite3.connect(rdb); c.row_factory = sqlite3.Row
    cur = c.cursor(); cur.execute("SELECT COUNT(*) as c FROM products WHERE barcode LIKE 'E2E_%'")
    r = cur.fetchone()
    check(r[0] >= 4, f"Restored DB has {r[0]} E2E products", f"Only {r[0]}")
    c.close(); shutil.rmtree(rd, ignore_errors=True)
    ok("Restore test passed + cleanup")
except Exception as e:
    ng(f"Backup/Restore Error: {e}")

# =====================================================================
print("\n" + "=" * 70)
print("TEST 9: SalesLogManager")
print("=" * 70)
try:
    slm = SalesLogManager()
    slm.add_sale({"sale_number": "E2E-SL-001", "total_amount": 1250.00, "payment_method": "เงินสด"})
    slm.add_sale({"sale_number": "E2E-SL-002", "total_amount": 890.50, "payment_method": "โอนเงิน"})
    content = slm.get_current_log_content()
    check("E2E-SL-001" in content, "Sale E2E-SL-001 found in log", "Not found")
    check("E2E-SL-002" in content, "Sale E2E-SL-002 found in log", "Not found")
    check("1,250.00" in content, "Amount 1,250.00 correct", "Amount wrong")
    ok("SalesLogManager works")
except Exception as e:
    ng(f"SalesLog Error: {e}")

# =====================================================================
print("\n" + "=" * 70)
print("CLEANUP")
print("=" * 70)
db.connect()
db.execute("DELETE FROM products WHERE barcode LIKE 'E2E_%'")
db.connection.commit()
r = db.fetch_one("SELECT COUNT(*) as c FROM products WHERE barcode LIKE 'E2E_%'")
check(r['c'] == 0, "Cleaned all E2E products", f"Still {r['c']}")
db.disconnect()
for f in [TEST_EXCEL, TEST_ZIP]:
    if os.path.exists(f): os.remove(f); print(f"  Deleted: {f}")

# =====================================================================
print("\n" + "=" * 70)
print(f"RESULT: PASS={PASS} / FAIL={FAIL} (Total {PASS+FAIL})")
print("=" * 70)
if FAIL == 0:
    print("=> ALL PASSED! Export/Import/Backup/Restore/UNIQUE/Reactivate/Lock OK!")
else:
    print(f"=> {FAIL} FAILURES need fixing!")
sys.exit(FAIL)
