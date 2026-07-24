# -*- coding: utf-8 -*-
"""
🔬 Database Stress Test — ทดสอบความแข็งแรงและสอดคล้องของ Database
ครอบคลุม:
  1. Integrity Check (PRAGMA integrity_check, foreign_key_check)
  2. Backup → Restore Round-trip (ZIP)
  3. Scalability: เพิ่มสินค้า 500 / 1000 รายการ + ยอดขาย
  4. Concurrent Access (Multi-thread read/write)
  5. Query Performance Benchmark (ค้นหา, Aggregate, JOIN)
  6. Transaction Rollback Safety
"""

import sys
import os
import time
import random
import string
import threading
import tempfile
import shutil
import zipfile
import sqlite3
import gc
from pathlib import Path
from datetime import datetime, timedelta

# เพิ่มพาธโปรเจกต์
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database.db_manager import DatabaseManager
from config import DATABASE_PATH

# ===== ค่าคงที่สำหรับการทดสอบ =====
TEST_DB_PATH = Path(__file__).resolve().parent / "stress_test.db"
PRODUCT_COUNTS = [500, 1000]  # ทดสอบทั้ง 500 และ 1000 รายการ

# ข้อมูลจำลองภาษาไทย
THAI_PRODUCT_PREFIXES = [
    "น้ำดื่ม", "นมสด", "กาแฟ", "ชาเขียว", "น้ำอัดลม", "ขนมปัง", "บะหมี่กึ่งสำเร็จ",
    "สบู่", "แชมพู", "ยาสีฟัน", "ผงซักฟอก", "น้ำยาล้างจาน", "กระดาษทิชชู่", "ข้าวสาร",
    "น้ำมันพืช", "น้ำปลา", "ซอสพริก", "น้ำตาลทราย", "เกลือ", "พริกไทย", "ไข่ไก่",
    "นมข้นหวาน", "ครีมเทียม", "ชาดำ", "โอวัลติน", "มันฝรั่งทอด", "ขนมปี๊บ",
    "ปลากระป๋อง", "ทูน่ากระป๋อง", "ข้าวโพดกระป๋อง", "ถั่วลิสง", "เม็ดมะม่วงหิมพานต์",
    "ลูกอม", "หมากฝรั่ง", "ช็อกโกแลต", "ไอศกรีม", "วุ้นเส้น", "เส้นหมี่", "เส้นใหญ่",
    "แป้งสาลี", "แป้งข้าวเจ้า", "แบตเตอรี่", "หลอดไฟ", "ปลั๊กพ่วง", "สายชาร์จ",
    "เมาส์", "คีย์บอร์ด", "หูฟัง", "ลำโพง", "เคสโทรศัพท์", "ฟิล์มกระจก",
]

THAI_BRANDS = [
    "ตราสิงห์", "ตราช้าง", "โฟร์โมสต์", "เบอร์ดี้", "โค้ก", "เป็ปซี่", "เลย์",
    "มาม่า", "ไวไว", "ยำยำ", "ซันซิลค์", "ดาวน์นี่", "คอลเกต", "ไลอ้อน",
    "ออรัล-บี", "โตโต้", "เอเฟ่", "บิ๊กซี", "เทสโก้", "แม็คโคร",
]

THAI_CATEGORIES = [
    "เครื่องดื่ม", "ขนมขบเคี้ยว", "อาหารกระป๋อง", "ของใช้ในบ้าน",
    "เครื่องสำอาง", "อุปกรณ์ไฟฟ้า", "เครื่องเขียน", "อาหารสด",
]


def generate_barcode(idx):
    """สร้างบาร์โค้ด EAN-13 จำลอง"""
    return f"88500{idx:08d}"


def generate_product_name(idx):
    """สร้างชื่อสินค้าภาษาไทย"""
    prefix = THAI_PRODUCT_PREFIXES[idx % len(THAI_PRODUCT_PREFIXES)]
    brand = THAI_BRANDS[idx % len(THAI_BRANDS)]
    size = random.choice(["100มล", "250มล", "500มล", "1ลิตร", "50ก", "100ก", "200ก", "500ก", "1กก"])
    return f"{prefix} {brand} {size}"


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_result(test_name, passed, detail="", elapsed=None):
    status = "✅ PASS" if passed else "❌ FAIL"
    time_str = f" ({elapsed:.3f}s)" if elapsed is not None else ""
    print(f"  {status} {test_name}{time_str}")
    if detail:
        print(f"         {detail}")


class StressTestRunner:
    def __init__(self):
        self.results = []
        self.test_db_path = str(TEST_DB_PATH)

    def setup_test_db(self):
        """สร้างฐานข้อมูลทดสอบแยกไม่กระทบข้อมูลจริง"""
        # ปิด connection ทั้งหมดก่อนลบไฟล์ (ป้องกัน WinError 32)
        DatabaseManager.close_all_connections()
        gc.collect()
        time.sleep(0.5)

        # ลบ DB เก่าถ้ามี
        for suffix in ["", "-wal", "-shm"]:
            p = Path(self.test_db_path + suffix)
            if p.exists():
                for attempt in range(3):
                    try:
                        p.unlink()
                        break
                    except PermissionError:
                        gc.collect()
                        time.sleep(0.5)

        DatabaseManager._schema_upgraded = False
        db = DatabaseManager(self.test_db_path)
        db.connect()
        db.initialize_database()
        db.disconnect()
        DatabaseManager._schema_upgraded = False  # reset สำหรับ test DB

    def cleanup(self):
        """ลบ DB ทดสอบ"""
        DatabaseManager.close_all_connections()
        gc.collect()
        time.sleep(0.5)
        for suffix in ["", "-wal", "-shm"]:
            p = Path(self.test_db_path + suffix)
            if p.exists():
                for attempt in range(3):
                    try:
                        p.unlink()
                        break
                    except Exception:
                        gc.collect()
                        time.sleep(0.5)

    # ============================================================
    # TEST 1: Database Integrity Check
    # ============================================================
    def test_integrity_check(self):
        print_header("TEST 1: Database Integrity Check (ฐานข้อมูลจริง)")

        db = DatabaseManager()
        ok, msg = db.check_integrity()
        print_result("PRAGMA integrity_check", ok, msg)
        self.results.append(("Integrity Check", ok))

        ok_fk, msg_fk = db.check_foreign_keys()
        print_result("PRAGMA foreign_key_check", ok_fk, msg_fk)
        self.results.append(("Foreign Key Check", ok_fk))

        # ตรวจสอบ Index ที่ควรมี
        db.connect()
        indexes = db.fetch_all("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        db.disconnect()
        idx_names = [i['name'] for i in indexes] if indexes else []
        critical_indexes = [
            "idx_products_barcode", "idx_products_name", "idx_sales_number",
            "idx_sales_date", "idx_sale_items_sale_id"
        ]
        missing = [i for i in critical_indexes if i not in idx_names]
        idx_ok = len(missing) == 0
        print_result(
            f"Critical Indexes ({len(critical_indexes)} required)",
            idx_ok,
            f"Missing: {missing}" if missing else f"All {len(critical_indexes)} indexes present"
        )
        self.results.append(("Critical Indexes", idx_ok))

    # ============================================================
    # TEST 2: Scalability — เพิ่มสินค้า 500 / 1000 รายการ
    # ============================================================
    def test_scalability(self):
        print_header("TEST 2: Scalability — เพิ่มสินค้า 500 & 1000 รายการ")

        for target_count in PRODUCT_COUNTS:
            self.setup_test_db()
            db = DatabaseManager(self.test_db_path)
            db.connect()

            # สร้างหมวดหมู่
            for i, cat in enumerate(THAI_CATEGORIES, 1):
                db.execute(
                    "INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (?, ?)",
                    (i, cat)
                )

            # เพิ่มสินค้าจำนวนมาก ด้วย batch transaction
            t_start = time.perf_counter()
            db.begin_transaction()

            for idx in range(1, target_count + 1):
                barcode = generate_barcode(idx)
                name = generate_product_name(idx)
                cat_id = (idx % len(THAI_CATEGORIES)) + 1
                cost = round(random.uniform(5, 500), 2)
                retail = round(cost * random.uniform(1.2, 2.5), 2)
                wholesale = round(cost * random.uniform(1.1, 1.8), 2)
                stock = random.randint(0, 1000)
                min_stock = random.randint(5, 50)

                db.execute("""
                    INSERT INTO products (
                        barcode, product_name, category_id,
                        cost_price, retail_price, wholesale_price,
                        stock_quantity, min_stock, unit, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (barcode, name, cat_id, cost, retail, wholesale, stock, min_stock, "ชิ้น"))

            db.commit_transaction()
            t_insert = time.perf_counter() - t_start

            # ตรวจสอบจำนวนที่เพิ่ม
            row = db.fetch_one("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
            actual_count = row['cnt'] if row else 0
            ok = actual_count == target_count
            print_result(
                f"INSERT {target_count} products (batch transaction)",
                ok,
                f"Actual: {actual_count} rows",
                t_insert
            )
            self.results.append((f"Insert {target_count} products", ok))

            # --- ทดสอบการค้นหา ---
            t_search = time.perf_counter()
            results = db.fetch_all(
                "SELECT * FROM products WHERE product_name LIKE ? AND is_active = 1 LIMIT 30",
                ("%น้ำดื่ม%",)
            )
            t_search = time.perf_counter() - t_search
            search_ok = len(results) > 0
            print_result(
                f"LIKE search in {target_count} products",
                search_ok,
                f"Found {len(results)} results",
                t_search
            )
            self.results.append((f"Search {target_count} products", search_ok))

            # --- ทดสอบ barcode lookup (should be O(1) via index) ---
            test_barcode = generate_barcode(target_count // 2)
            t_barcode = time.perf_counter()
            for _ in range(100):  # 100 lookups
                db.fetch_one("SELECT * FROM products WHERE barcode = ?", (test_barcode,))
            t_barcode = (time.perf_counter() - t_barcode)
            avg_barcode_ms = (t_barcode / 100) * 1000
            barcode_ok = avg_barcode_ms < 5  # ต้องใช้เวลาน้อยกว่า 5ms ต่อครั้ง
            print_result(
                f"Barcode lookup (100x avg) in {target_count} products",
                barcode_ok,
                f"Avg: {avg_barcode_ms:.3f}ms per lookup",
                t_barcode
            )
            self.results.append((f"Barcode lookup {target_count}", barcode_ok))

            # --- ทดสอบ Aggregate query ---
            t_agg = time.perf_counter()
            agg = db.fetch_one("""
                SELECT 
                    COUNT(*) as total,
                    SUM(stock_quantity) as total_stock,
                    AVG(retail_price) as avg_price,
                    MIN(retail_price) as min_price,
                    MAX(retail_price) as max_price
                FROM products WHERE is_active = 1
            """)
            t_agg = time.perf_counter() - t_agg
            agg_ok = agg and agg['total'] == target_count
            print_result(
                f"Aggregate query (COUNT/SUM/AVG/MIN/MAX) on {target_count}",
                agg_ok,
                f"Total stock: {agg['total_stock']:,.0f}, Avg price: ฿{agg['avg_price']:.2f}",
                t_agg
            )
            self.results.append((f"Aggregate {target_count}", agg_ok))

            # --- ทดสอบ GROUP BY (Report query) ---
            t_group = time.perf_counter()
            groups = db.fetch_all("""
                SELECT c.category_name, COUNT(*) as cnt, SUM(p.stock_quantity) as total_stock
                FROM products p
                JOIN categories c ON p.category_id = c.category_id
                WHERE p.is_active = 1
                GROUP BY c.category_id
                ORDER BY cnt DESC
            """)
            t_group = time.perf_counter() - t_group
            group_ok = len(groups) == len(THAI_CATEGORIES)
            print_result(
                f"GROUP BY with JOIN on {target_count}",
                group_ok,
                f"Categories: {len(groups)}",
                t_group
            )
            self.results.append((f"GroupBy {target_count}", group_ok))

            db.disconnect()
            DatabaseManager.close_all_connections()
            gc.collect()

    # ============================================================
    # TEST 3: Backup & Restore Round-trip (ZIP)
    # ============================================================
    def test_backup_restore(self):
        print_header("TEST 3: Backup → Restore Round-trip (ZIP)")

        self.setup_test_db()
        db = DatabaseManager(self.test_db_path)
        db.connect()

        # สร้างหมวดหมู่
        for i, cat in enumerate(THAI_CATEGORIES, 1):
            db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (?, ?)", (i, cat))

        # เพิ่มสินค้า 200 รายการ
        BACKUP_TEST_COUNT = 200
        db.begin_transaction()
        for idx in range(1, BACKUP_TEST_COUNT + 1):
            barcode = generate_barcode(idx)
            name = generate_product_name(idx)
            cat_id = (idx % len(THAI_CATEGORIES)) + 1
            cost = round(random.uniform(5, 300), 2)
            retail = round(cost * 1.5, 2)
            db.execute("""
                INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price, stock_quantity, unit, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 'ชิ้น', 1)
            """, (barcode, name, cat_id, cost, retail, random.randint(10, 500)))
        db.commit_transaction()

        # เพิ่มยอดขายจำลอง
        db.begin_transaction()
        for s_idx in range(1, 51):  # 50 ยอดขาย
            sale_num = f"SL20260724{s_idx:04d}"
            sale_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S")
            total = round(random.uniform(50, 5000), 2)
            db.execute("""
                INSERT INTO sales (sale_number, sale_date, user_id, subtotal, total_amount, paid_amount, payment_method, status)
                VALUES (?, ?, 1, ?, ?, ?, 'cash', 'completed')
            """, (sale_num, sale_date, total, total, total))
            
            sale_row = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (sale_num,))
            if sale_row:
                # 1-5 รายการต่อใบเสร็จ
                for item_i in range(random.randint(1, 5)):
                    prod_id = random.randint(1, BACKUP_TEST_COUNT)
                    qty = random.randint(1, 10)
                    price = round(random.uniform(10, 200), 2)
                    db.execute("""
                        INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (sale_row['sale_id'], prod_id, f"สินค้า #{prod_id}", qty, price, round(qty * price, 2)))
        db.commit_transaction()

        # ดึงข้อมูลก่อน Backup
        before_products = db.fetch_one("SELECT COUNT(*) as cnt FROM products")['cnt']
        before_sales = db.fetch_one("SELECT COUNT(*) as cnt FROM sales")['cnt']
        before_items = db.fetch_one("SELECT COUNT(*) as cnt FROM sale_items")['cnt']
        before_checksum = db.fetch_one("SELECT SUM(retail_price) as s FROM products")['s']

        db.disconnect()

        # --- สร้าง Backup ZIP ---
        backup_zip = Path(tempfile.mktemp(suffix=".zip"))
        t_backup = time.perf_counter()

        try:
            # Flush WAL
            conn = sqlite3.connect(self.test_db_path, timeout=15.0)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
        except Exception:
            pass

        with zipfile.ZipFile(str(backup_zip), 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.test_db_path, "database.db")

        t_backup = time.perf_counter() - t_backup
        backup_size_kb = backup_zip.stat().st_size / 1024
        print_result(
            "Backup to ZIP",
            backup_zip.exists(),
            f"Size: {backup_size_kb:.1f} KB",
            t_backup
        )
        self.results.append(("Backup ZIP", backup_zip.exists()))

        # --- ลบ DB เดิม (จำลอง Reset) ---
        DatabaseManager.close_all_connections()
        gc.collect()
        time.sleep(0.3)
        for suffix in ["", "-wal", "-shm"]:
            p = Path(self.test_db_path + suffix)
            if p.exists():
                p.unlink()

        # --- Restore จาก ZIP ---
        t_restore = time.perf_counter()
        temp_dir = Path(tempfile.mkdtemp())

        with zipfile.ZipFile(str(backup_zip), 'r') as zipf:
            for member in zipf.infolist():
                if "__MACOSX" in member.filename or member.filename.endswith(".DS_Store"):
                    continue
                zipf.extract(member, temp_dir)

        restored_db = temp_dir / "database.db"
        if restored_db.exists():
            shutil.copy2(restored_db, self.test_db_path)

        t_restore = time.perf_counter() - t_restore
        restore_ok = Path(self.test_db_path).exists()
        print_result("Restore from ZIP", restore_ok, elapsed=t_restore)
        self.results.append(("Restore ZIP", restore_ok))

        # --- ตรวจสอบความสอดคล้องของข้อมูลหลัง Restore ---
        DatabaseManager._schema_upgraded = False
        db = DatabaseManager(self.test_db_path)
        db.connect()

        after_products = db.fetch_one("SELECT COUNT(*) as cnt FROM products")['cnt']
        after_sales = db.fetch_one("SELECT COUNT(*) as cnt FROM sales")['cnt']
        after_items = db.fetch_one("SELECT COUNT(*) as cnt FROM sale_items")['cnt']
        after_checksum = db.fetch_one("SELECT SUM(retail_price) as s FROM products")['s']

        db.disconnect()

        # ตรวจจำนวนสินค้า
        prod_match = before_products == after_products
        print_result(
            "Product count match",
            prod_match,
            f"Before: {before_products} → After: {after_products}"
        )
        self.results.append(("Restore product count", prod_match))

        # ตรวจจำนวนยอดขาย
        sales_match = before_sales == after_sales
        print_result(
            "Sales count match",
            sales_match,
            f"Before: {before_sales} → After: {after_sales}"
        )
        self.results.append(("Restore sales count", sales_match))

        # ตรวจจำนวน sale items
        items_match = before_items == after_items
        print_result(
            "Sale items count match",
            items_match,
            f"Before: {before_items} → After: {after_items}"
        )
        self.results.append(("Restore sale items count", items_match))

        # ตรวจ Checksum (SUM ราคา)
        checksum_match = abs((before_checksum or 0) - (after_checksum or 0)) < 0.01
        print_result(
            "Price checksum match (SUM retail_price)",
            checksum_match,
            f"Before: ฿{before_checksum:,.2f} → After: ฿{after_checksum:,.2f}"
        )
        self.results.append(("Restore checksum", checksum_match))

        # Integrity check หลัง restore
        db2 = DatabaseManager(self.test_db_path)
        ok_int, msg_int = db2.check_integrity()
        print_result("Integrity after restore", ok_int, msg_int)
        self.results.append(("Integrity after restore", ok_int))

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        try:
            backup_zip.unlink()
        except Exception:
            pass

    # ============================================================
    # TEST 4: Concurrent Access (Multi-thread)
    # ============================================================
    def test_concurrent_access(self):
        print_header("TEST 4: Concurrent Access — Multi-thread Read/Write")

        self.setup_test_db()
        db_init = DatabaseManager(self.test_db_path)
        db_init.connect()

        # สร้างหมวดหมู่และสินค้าพื้นฐาน
        for i, cat in enumerate(THAI_CATEGORIES, 1):
            db_init.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (?, ?)", (i, cat))

        for idx in range(1, 101):
            db_init.execute("""
                INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price, stock_quantity, unit, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 'ชิ้น', 1)
            """, (generate_barcode(idx), generate_product_name(idx), (idx % 8) + 1, 50.0, 100.0, 500))
        db_init.disconnect()

        errors = []
        operations_done = {'read': 0, 'write': 0}
        lock = threading.Lock()

        def writer_thread(thread_id, iterations=20):
            """Thread สำหรับเขียนข้อมูล"""
            try:
                conn = sqlite3.connect(self.test_db_path, timeout=15.0)
                conn.execute("PRAGMA busy_timeout = 15000")
                conn.execute("PRAGMA journal_mode=WAL")
                cursor = conn.cursor()
                for i in range(iterations):
                    prod_id = random.randint(1, 100)
                    new_stock = random.randint(0, 1000)
                    cursor.execute(
                        "UPDATE products SET stock_quantity = ? WHERE product_id = ?",
                        (new_stock, prod_id)
                    )
                    conn.commit()
                    with lock:
                        operations_done['write'] += 1
                conn.close()
            except Exception as e:
                with lock:
                    errors.append(f"Writer-{thread_id}: {e}")

        def reader_thread(thread_id, iterations=50):
            """Thread สำหรับอ่านข้อมูล"""
            try:
                conn = sqlite3.connect(self.test_db_path, timeout=15.0)
                conn.execute("PRAGMA busy_timeout = 15000")
                conn.execute("PRAGMA journal_mode=WAL")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                for i in range(iterations):
                    cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active = 1")
                    cursor.fetchone()
                    cursor.execute("SELECT * FROM products WHERE product_id = ?", (random.randint(1, 100),))
                    cursor.fetchone()
                    with lock:
                        operations_done['read'] += 1
                conn.close()
            except Exception as e:
                with lock:
                    errors.append(f"Reader-{thread_id}: {e}")

        # สร้าง 3 writer + 5 reader threads
        t_start = time.perf_counter()
        threads = []
        for i in range(3):
            t = threading.Thread(target=writer_thread, args=(i,))
            threads.append(t)
        for i in range(5):
            t = threading.Thread(target=reader_thread, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        t_concurrent = time.perf_counter() - t_start

        no_errors = len(errors) == 0
        total_ops = operations_done['read'] + operations_done['write']
        print_result(
            f"Concurrent R/W (3 writers + 5 readers)",
            no_errors,
            f"Total ops: {total_ops} (Read: {operations_done['read']}, Write: {operations_done['write']})"
            + (f"\nErrors: {errors[:3]}" if errors else ""),
            t_concurrent
        )
        self.results.append(("Concurrent Access", no_errors))

    # ============================================================
    # TEST 5: Transaction Rollback Safety
    # ============================================================
    def test_transaction_rollback(self):
        print_header("TEST 5: Transaction Rollback Safety")

        self.setup_test_db()
        db = DatabaseManager(self.test_db_path)
        db.connect()

        # สร้างหมวดหมู่และสินค้า
        db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (1, 'ทดสอบ')")
        for idx in range(1, 11):
            db.execute("""
                INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price, stock_quantity, unit, is_active)
                VALUES (?, ?, 1, 50, 100, 100, 'ชิ้น', 1)
            """, (generate_barcode(idx), f"สินค้าทดสอบ #{idx}"))

        before_count = db.fetch_one("SELECT COUNT(*) as cnt FROM products")['cnt']

        # เริ่ม transaction แล้ว rollback
        db.begin_transaction()
        for idx in range(11, 21):
            db.execute("""
                INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price, stock_quantity, unit, is_active)
                VALUES (?, ?, 1, 50, 100, 100, 'ชิ้น', 1)
            """, (generate_barcode(idx), f"สินค้าที่ต้องถูก Rollback #{idx}"))
        db.rollback_transaction()

        after_count = db.fetch_one("SELECT COUNT(*) as cnt FROM products")['cnt']
        rollback_ok = before_count == after_count
        print_result(
            "Transaction rollback",
            rollback_ok,
            f"Before: {before_count} → After rollback: {after_count} (should be equal)"
        )
        self.results.append(("Transaction Rollback", rollback_ok))

        db.disconnect()

    # ============================================================
    # TEST 6: Large Sale Simulation (ห้างขนาดกลาง)
    # ============================================================
    def test_large_sale_simulation(self):
        print_header("TEST 6: Large Sale Simulation (ห้างขนาดกลาง — 1 วัน)")

        self.setup_test_db()
        db = DatabaseManager(self.test_db_path)
        db.connect()

        # สร้างหมวดหมู่ + สินค้า 500 รายการ
        for i, cat in enumerate(THAI_CATEGORIES, 1):
            db.execute("INSERT OR IGNORE INTO categories (category_id, category_name) VALUES (?, ?)", (i, cat))

        db.begin_transaction()
        for idx in range(1, 501):
            db.execute("""
                INSERT INTO products (barcode, product_name, category_id, cost_price, retail_price, stock_quantity, unit, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 'ชิ้น', 1)
            """, (generate_barcode(idx), generate_product_name(idx), (idx % 8) + 1,
                  round(random.uniform(5, 300), 2), round(random.uniform(15, 600), 2), random.randint(50, 1000)))
        db.commit_transaction()

        # จำลองยอดขาย 1 วัน: 200 ใบเสร็จ, แต่ละใบ 3-15 รายการ
        DAILY_SALES = 200
        t_sales = time.perf_counter()
        total_items_inserted = 0

        db.begin_transaction()
        for s_idx in range(1, DAILY_SALES + 1):
            sale_num = f"SL20260724{s_idx:04d}"
            hour = random.randint(8, 21)
            minute = random.randint(0, 59)
            sale_date = f"2026-07-24 {hour:02d}:{minute:02d}:00"
            items_count = random.randint(3, 15)

            subtotal = 0
            items_data = []
            for _ in range(items_count):
                prod_id = random.randint(1, 500)
                qty = random.randint(1, 5)
                price = round(random.uniform(10, 300), 2)
                item_total = round(qty * price, 2)
                subtotal += item_total
                items_data.append((prod_id, qty, price, item_total))

            total = round(subtotal, 2)
            payment = random.choice(['cash', 'transfer', 'credit'])

            db.execute("""
                INSERT INTO sales (sale_number, sale_date, user_id, subtotal, total_amount, paid_amount, payment_method, status)
                VALUES (?, ?, 1, ?, ?, ?, ?, 'completed')
            """, (sale_num, sale_date, subtotal, total, total + random.randint(0, 100), payment))

            sale_row = db.fetch_one("SELECT sale_id FROM sales WHERE sale_number = ?", (sale_num,))
            if sale_row:
                for prod_id, qty, price, item_total in items_data:
                    db.execute("""
                        INSERT INTO sale_items (sale_id, product_id, product_name, quantity, unit_price, total_price)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (sale_row['sale_id'], prod_id, f"สินค้า #{prod_id}", qty, price, item_total))
                    total_items_inserted += 1

        db.commit_transaction()
        t_sales = time.perf_counter() - t_sales

        # ตรวจสอบจำนวน
        sales_count = db.fetch_one("SELECT COUNT(*) as cnt FROM sales")['cnt']
        items_count = db.fetch_one("SELECT COUNT(*) as cnt FROM sale_items")['cnt']
        sales_ok = sales_count == DAILY_SALES
        print_result(
            f"Insert {DAILY_SALES} sales with {total_items_inserted} items",
            sales_ok,
            f"Sales: {sales_count}, Items: {items_count}",
            t_sales
        )
        self.results.append((f"Daily Sales {DAILY_SALES}", sales_ok))

        # ทดสอบ Daily Report query
        t_report = time.perf_counter()
        report = db.fetch_one("""
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_sale,
                COUNT(CASE WHEN payment_method = 'cash' THEN 1 END) as cash_count,
                COUNT(CASE WHEN payment_method = 'transfer' THEN 1 END) as transfer_count
            FROM sales WHERE sale_date LIKE '2026-07-24%'
        """)
        t_report = time.perf_counter() - t_report
        report_ok = report and report['total_sales'] == DAILY_SALES
        print_result(
            "Daily report aggregate query",
            report_ok,
            f"Revenue: ฿{report['total_revenue']:,.2f}, Avg: ฿{report['avg_sale']:,.2f}",
            t_report
        )
        self.results.append(("Daily Report Query", report_ok))

        # ทดสอบ Best-selling products query
        t_best = time.perf_counter()
        best = db.fetch_all("""
            SELECT si.product_name, SUM(si.quantity) as total_qty, SUM(si.total_price) as total_revenue
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.sale_id
            WHERE s.sale_date LIKE '2026-07-24%'
            GROUP BY si.product_id
            ORDER BY total_qty DESC
            LIMIT 10
        """)
        t_best = time.perf_counter() - t_best
        best_ok = len(best) > 0
        print_result(
            "Top 10 best-selling products query",
            best_ok,
            f"Top seller: {best[0]['product_name']} ({best[0]['total_qty']} qty)" if best else "No data",
            t_best
        )
        self.results.append(("Best-selling Query", best_ok))

        db.disconnect()

    # ============================================================
    # TEST 7: Database Size Estimation
    # ============================================================
    def test_db_size_estimation(self):
        print_header("TEST 7: Database Size Estimation — ขนาดไฟล์สำหรับห้างระดับกลาง")

        # ใช้ข้อมูลจาก test ก่อนหน้า
        if Path(self.test_db_path).exists():
            # Checkpoint WAL
            try:
                conn = sqlite3.connect(self.test_db_path, timeout=15.0)
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
            except Exception:
                pass

            db_size_mb = Path(self.test_db_path).stat().st_size / (1024 * 1024)
            # ประมาณการณ์สำหรับ 1 ปี (200 sales/day * 365 days)
            est_yearly_mb = db_size_mb * 365
            size_ok = db_size_mb < 100  # ต้องไม่เกิน 100MB สำหรับข้อมูล 1 วัน
            print_result(
                "Current test DB size",
                size_ok,
                f"Size: {db_size_mb:.2f} MB"
            )
            print_result(
                "Estimated 1-year DB size (200 sales/day)",
                est_yearly_mb < 2000,
                f"~{est_yearly_mb:.0f} MB ({est_yearly_mb/1024:.1f} GB) — SQLite limit: 281 TB"
            )
            self.results.append(("DB Size OK", size_ok))
        else:
            print_result("DB Size", False, "Test DB not found")
            self.results.append(("DB Size OK", False))

    # ============================================================
    # Summary
    # ============================================================
    def print_summary(self):
        print_header("📊 SUMMARY — ผลการทดสอบทั้งหมด")

        passed = sum(1 for _, ok in self.results if ok)
        failed = sum(1 for _, ok in self.results if not ok)
        total = len(self.results)

        for name, ok in self.results:
            status = "✅" if ok else "❌"
            print(f"  {status} {name}")

        print(f"\n  {'='*50}")
        print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")

        if failed == 0:
            print(f"\n  🎉 ALL TESTS PASSED!")
            print(f"  ✅ Database พร้อมรองรับห้างระดับกลาง 500-1000 รายการ")
            print(f"  ✅ Backup/Restore ทำงานถูกต้อง 100%")
            print(f"  ✅ Concurrent Access ปลอดภัย")
            print(f"  ✅ Transaction Rollback ทำงานถูกต้อง")
        else:
            print(f"\n  ⚠️ มีบางรายการที่ไม่ผ่าน กรุณาตรวจสอบ!")

        return failed == 0

    def run_all(self):
        """รันการทดสอบทั้งหมด"""
        print("\n" + "🔬" * 35)
        print("  Database Stress Test — Store POS")
        print("  เริ่มทดสอบ:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("🔬" * 35)

        t_total = time.perf_counter()

        try:
            self.test_integrity_check()
            self.test_scalability()
            self.test_backup_restore()
            self.test_concurrent_access()
            self.test_transaction_rollback()
            self.test_large_sale_simulation()
            self.test_db_size_estimation()
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        t_total = time.perf_counter() - t_total
        print(f"\n  ⏱️ Total execution time: {t_total:.2f}s")

        return self.print_summary()


if __name__ == "__main__":
    runner = StressTestRunner()
    all_passed = runner.run_all()
    sys.exit(0 if all_passed else 1)
