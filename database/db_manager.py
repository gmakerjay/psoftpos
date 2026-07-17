# -*- coding: utf-8 -*-
"""
ระบบจัดการฐานข้อมูล SQLite
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
import bcrypt
from config import DATABASE_PATH
from utils.logger import log_database_query, log_error, log_info


class DatabaseManager:
    """จัดการการเชื่อมต่อและดำเนินการกับฐานข้อมูล - Optimized"""
    
    # Connection pool สำหรับลดการเปิด-ปิด connection บ่อย
    _connection_pool = {}
    _pool_size = 3
    try:
        import performance_config
        _pool_size = performance_config.DB_CONNECTION_POOL_SIZE
    except ImportError:
        pass
    _pool_lock = threading.Lock()  # Thread-safe pool access
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self.connection = None
        self.cursor = None
        self.last_error = None
        self._use_pool = True  # ใช้ connection pool
        try:
            import performance_config
            self._use_pool = performance_config.USE_CONNECTION_POOL
        except ImportError:
            pass
        self._in_transaction = False  # ติดตามสถานะ transaction

    def _check_and_auto_init(self):
        """ตรวจสอบและสร้างตารางฐานข้อมูลอัตโนมัติหากยังไม่มี เพื่อป้องกันปัญหา no such table"""
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
            if not self.cursor.fetchone():
                log_info("Database tables missing. Auto-initializing database...")
                self.initialize_database()
            else:
                self._upgrade_database_schema()
        except Exception as e:
            log_error(f"Error auto-initializing database: {e}")

    def _upgrade_database_schema(self):
        """อัปเกรดฐานข้อมูลแบบปลอดภัย (รักษาความเข้ากันได้ย้อนหลัง)"""
        try:
            # 0. สร้างตารางบันทึกประวัติ License
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS license_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT,
                    license_key TEXT,
                    hwid TEXT,
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 1. สร้างตารางระดับสมาชิกและสมาชิกถ้ายังไม่มี
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS member_tiers (
                    tier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tier_name TEXT UNIQUE NOT NULL,
                    discount_percent REAL DEFAULT 0.0,
                    min_points INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # ใส่ระดับสมาชิกเริ่มต้นถ้าตารางว่าง
            self.cursor.execute("SELECT COUNT(*) FROM member_tiers")
            row = self.cursor.fetchone()
            if row and row[0] == 0:
                tiers = [
                    ("สมาชิกทั่วไป (General)", 0.0, 0),
                    ("สมาชิกระดับเงิน (Silver)", 5.0, 100),
                    ("สมาชิกระดับทอง (Gold)", 10.0, 500),
                    ("สมาชิกระดับแพลทินัม (Platinum)", 15.0, 1000),
                    ("สมาชิกพิเศษ (VIP)", 20.0, 5000)
                ]
                for name, disc, pts in tiers:
                    self.cursor.execute(
                        "INSERT OR IGNORE INTO member_tiers (tier_name, discount_percent, min_points) VALUES (?, ?, ?)",
                        (name, disc, pts)
                    )
            else:
                # อัปเดตระดับสมาชิกเดิมให้เป็นภาษาไทยที่อ่านเข้าใจง่าย
                self.cursor.execute("UPDATE OR IGNORE member_tiers SET tier_name = 'สมาชิกทั่วไป (General)' WHERE tier_name = 'General'")
                self.cursor.execute("UPDATE OR IGNORE member_tiers SET tier_name = 'สมาชิกระดับเงิน (Silver)' WHERE tier_name = 'Silver'")
                self.cursor.execute("UPDATE OR IGNORE member_tiers SET tier_name = 'สมาชิกระดับทอง (Gold)' WHERE tier_name = 'Gold'")
                self.cursor.execute("UPDATE OR IGNORE member_tiers SET tier_name = 'สมาชิกระดับแพลทินัม (Platinum)' WHERE tier_name = 'Platinum'")
                self.cursor.execute("UPDATE OR IGNORE member_tiers SET tier_name = 'สมาชิกพิเศษ (VIP)' WHERE tier_name = 'VIP'")
            
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    username TEXT UNIQUE,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expire_date TEXT,
                    license_count INTEGER DEFAULT 0,
                    notes TEXT,
                    tier_id INTEGER,
                    credit_balance REAL DEFAULT 0.0,
                    points INTEGER DEFAULT 0,
                    wallet_balance REAL DEFAULT 0.0,
                    discount_type TEXT DEFAULT 'none',
                    discount_value REAL DEFAULT 0.0,
                    discount_duration TEXT DEFAULT 'permanent',
                    discount_start_date TEXT,
                    discount_end_date TEXT,
                    FOREIGN KEY (tier_id) REFERENCES member_tiers (tier_id)
                )
            """)
            
            # 2. เพิ่มคอลัมน์ member_id ในตาราง sales ถ้ายังไม่มี
            self.cursor.execute("PRAGMA table_info(sales)")
            columns = [col[1] for col in self.cursor.fetchall()]
            if 'member_id' not in columns:
                log_info("Altering sales table to add member_id column...")
                self.cursor.execute("ALTER TABLE sales ADD COLUMN member_id INTEGER REFERENCES members(member_id)")
                
            # เพิ่มคอลัมน์ payment_details (สำหรับช่องทางการชำระเงินที่หลากหลาย) ในตาราง sales ถ้ายังไม่มี
            if 'payment_details' not in columns:
                log_info("Altering sales table to add payment_details column...")
                self.cursor.execute("ALTER TABLE sales ADD COLUMN payment_details TEXT")
                
            # เพิ่มคอลัมน์ is_archived ในตาราง sales ถ้ายังไม่มี
            if 'is_archived' not in columns:
                log_info("Altering sales table to add is_archived column...")
                self.cursor.execute("ALTER TABLE sales ADD COLUMN is_archived INTEGER DEFAULT 0")
                
            # เพิ่มคอลัมน์ is_archived ในตาราง returns ถ้ายังไม่มี
            self.cursor.execute("PRAGMA table_info(returns)")
            returns_columns = [col[1] for col in self.cursor.fetchall()]
            if 'is_archived' not in returns_columns:
                log_info("Altering returns table to add is_archived column...")
                self.cursor.execute("ALTER TABLE returns ADD COLUMN is_archived INTEGER DEFAULT 0")
                
            # 3. สร้าง Index เพื่อความเร็วในการค้นหา
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_phone ON members(phone)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_members_name ON members(name)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_member ON sales(member_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_archived ON sales(is_archived)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_returns_archived ON returns(is_archived)")
            
        except Exception as e:
            log_error(f"Error upgrading database schema: {e}")
        
    def connect(self):
        """เชื่อมต่อฐานข้อมูล - ดึง connection จาก pool หรือสร้างใหม่"""
        if self.connection and self.cursor:
            return True
            
        try:
            if self._use_pool:
                with self._pool_lock:
                    # ค้นหา connection ที่ไม่ได้ใช้งาน
                    for conn_id, conn_info in self._connection_pool.items():
                        if not conn_info['in_use']:
                            conn_info['in_use'] = True
                            self.connection = conn_info['connection']
                            self.connection.row_factory = sqlite3.Row
                            self.cursor = self.connection.cursor()
                            self._check_and_auto_init()
                            return True
                    
                    # ถ้า pool ยังไม่เต็ม สร้าง connection ใหม่
                    if len(self._connection_pool) < self._pool_size:
                        conn = sqlite3.connect(self.db_path, check_same_thread=False)
                        conn.row_factory = sqlite3.Row
                        # === Performance PRAGMAs (สำคัญมากสำหรับคอมรุ่นเก่า) ===
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA journal_mode=WAL")       # WAL mode เร็วกว่า DELETE 2-5x
                        cursor.execute("PRAGMA synchronous=NORMAL")     # ลด disk I/O (ปลอดภัยเพียงพอ)
                        cursor.execute("PRAGMA cache_size=-8000")       # 8MB cache (default 2MB)
                        cursor.execute("PRAGMA temp_store=MEMORY")      # ใช้ RAM สำหรับ temp tables
                        cursor.execute("PRAGMA mmap_size=67108864")     # 64MB memory-mapped I/O
                        conn_id = id(conn)
                        self._connection_pool[conn_id] = {
                            'connection': conn,
                            'in_use': True
                        }
                        self.connection = conn
                        self.cursor = conn.cursor()
                        self._check_and_auto_init()
                        return True
            
            # Fallback: สร้าง connection ปกติ
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self._check_and_auto_init()
            return True
        except sqlite3.Error as e:
            log_error(f"Error connecting to database: {e}", exc_info=True)
            return False
            
    def disconnect(self):
        """ตัดการเชื่อมต่อฐานข้อมูล - คืน connection กลับ pool"""
        if self._use_pool and self.connection:
            with self._pool_lock:
                # คืน connection กลับ pool แทนการปิด
                conn_id = id(self.connection)
                if conn_id in self._connection_pool:
                    self._connection_pool[conn_id]['in_use'] = False
                    self.connection = None
                    self.cursor = None
                    self._in_transaction = False
                    return
        
        # Fallback: ปิด connection ปกติ
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            self.is_in_transaction = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @classmethod
    def close_all_connections(cls):
        """ปิด connection ทั้งหมดอย่างสมบูรณ์ (ป้องกัน WinError 32 ตอนลบไฟล์)"""
        with cls._pool_lock:
            for conn_id, conn_info in cls._connection_pool.items():
                try:
                    conn_info['connection'].close()
                except Exception as e:
                    pass
            cls._connection_pool.clear()
            
    def execute(self, query, params=None):
        """Execute SQL query — auto-commit ถ้าไม่อยู่ใน transaction"""
        self.last_error = None
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            # Auto-commit เฉพาะเมื่อไม่อยู่ใน transaction
            if not self._in_transaction:
                self.connection.commit()
            return True
        except sqlite3.Error as e:
            self.last_error = str(e)
            log_error(f"Error executing query: {e}\nSQL: {query}", exc_info=True)
            if not self._in_transaction:
                self.connection.rollback()
            return False
    
    def begin_transaction(self):
        """เริ่ม transaction — ป้องกันข้อมูลไม่สอดคล้องเมื่อมีหลาย operations"""
        self._in_transaction = True
        try:
            self.cursor.execute("BEGIN TRANSACTION")
            return True
        except sqlite3.Error as e:
            self.last_error = str(e)
            log_error(f"Error beginning transaction: {e}", exc_info=True)
            self._in_transaction = False
            return False
    
    def commit_transaction(self):
        """Commit transaction — บันทึกทุก operations ที่ทำไว้"""
        self._in_transaction = False
        try:
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            self.last_error = str(e)
            log_error(f"Error committing transaction: {e}", exc_info=True)
            self.connection.rollback()
            return False
    
    def rollback_transaction(self):
        """Rollback transaction — ยกเลิกทุก operations ที่ทำไว้"""
        self._in_transaction = False
        try:
            self.connection.rollback()
            return True
        except sqlite3.Error as e:
            self.last_error = str(e)
            log_error(f"Error rolling back transaction: {e}", exc_info=True)
            return False
            
    def fetch_one(self, query, params=None):
        """Fetch single row"""
        self.last_error = None
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            self.last_error = str(e)
            log_error(f"Error fetching data: {e}\nSQL: {query}", exc_info=True)
            return None
            
    def fetch_all(self, query, params=None):
        """Fetch all rows"""
        self.last_error = None
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            self.last_error = str(e)
            log_error(f"Error fetching data: {e}\nSQL: {query}", exc_info=True)
            return []
            
    def initialize_database(self):
        """สร้างตารางฐานข้อมูลทั้งหมด"""
        if not self.connect():
            return False
            
        # ตารางผู้ใช้
        self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ตารางหมวดหมู่สินค้า
        self.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ตารางแบรนด์สินค้า
        self.execute("""
            CREATE TABLE IF NOT EXISTS brands (
                brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ตารางผู้จัดจำหน่าย (Vendors)
        self.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                vendor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_name TEXT NOT NULL,
                contact_name TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                tax_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ตารางสินค้า
        self.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE,
                serial_number TEXT,
                product_name TEXT NOT NULL,
                category_id INTEGER,
                description TEXT,
                unit TEXT DEFAULT 'ชิ้น',
                cost_price REAL DEFAULT 0,
                retail_price REAL DEFAULT 0,
                wholesale_price REAL DEFAULT 0,
                special_price1 REAL DEFAULT 0,
                special_price2 REAL DEFAULT 0,
                stock_quantity INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                image_path TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories (category_id)
            )
        """)
        
        # ตารางการขาย
        self.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_number TEXT UNIQUE NOT NULL,
                sale_date TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                customer_name TEXT,
                price_type TEXT DEFAULT 'retail',
                subtotal REAL DEFAULT 0,
                discount_type TEXT DEFAULT 'amount',
                discount_value REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                change_amount REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'cash',
                status TEXT DEFAULT 'completed',
                is_archived INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # ตารางรายละเอียดการขาย
        self.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount_amount REAL DEFAULT 0,
                total_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales (sale_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)
        
        # ตารางการคืนสินค้า
        self.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE NOT NULL,
                sale_id INTEGER NOT NULL,
                return_date TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                return_type TEXT DEFAULT 'partial',
                total_amount REAL DEFAULT 0,
                reason TEXT,
                status TEXT DEFAULT 'completed',
                is_archived INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales (sale_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # ตารางรายละเอียดการคืนสินค้า
        self.execute("""
            CREATE TABLE IF NOT EXISTS return_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                FOREIGN KEY (return_id) REFERENCES returns (return_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            )
        """)
        
        # ตารางการเคลื่อนไหวสต็อก
        self.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_id INTEGER,
                reference_type TEXT,
                user_id INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (product_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # ตารางการพักการขาย
        self.execute("""
            CREATE TABLE IF NOT EXISTS parked_sales (
                park_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name TEXT,
                items_json TEXT NOT NULL,
                price_type TEXT DEFAULT 'retail',
                subtotal REAL DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # ตารางประวัติการเข้าใช้งาน
        self.execute("""
            CREATE TABLE IF NOT EXISTS login_history (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                login_time TEXT DEFAULT CURRENT_TIMESTAMP,
                logout_time TEXT,
                ip_address TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # ตารางการตั้งค่า
        self.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ใส่ค่าเริ่มต้นสำหรับเครื่องพิมพ์ XP-58IIH
        self.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('printer_type', 'thermal')")
        self.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('paper_size', '58mm')")
        self.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('printer_name', 'XP-58')")
        self.execute("INSERT OR IGNORE INTO settings (setting_key, setting_value) VALUES ('printer_codepage', '18 (Xprinter, เครื่องจีนส่วนใหญ่)')")
        
        # เพิ่ม Index เพื่อรองรับสินค้าจำนวนมาก (1000+)
        self.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_sales_number ON sales(sale_number)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id ON sale_items(sale_id)")
        
        # === Composite indexes สำหรับ query ที่ใช้บ่อย (Performance) ===
        self.execute("CREATE INDEX IF NOT EXISTS idx_products_active_stock ON products(is_active, stock_quantity)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_products_active_name ON products(is_active, product_name)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_sales_date_status ON sales(sale_date, status)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_sale_items_product ON sale_items(product_id)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)")
        
        # สร้างผู้ใช้ admin เริ่มต้น
        self._create_default_admin()
        
        # สร้างหมวดหมู่เริ่มต้น
        self._create_default_categories()
        
        # อัปเกรดฐานข้อมูลแบบปลอดภัย (สร้างตารางสมาชิก)
        self._upgrade_database_schema()
        
        self.disconnect()
        return True
        
    def _create_default_admin(self):
        """สร้างผู้ใช้เริ่มต้น (admin + cashier)"""
        # สร้าง admin ถ้ายังไม่มี
        result = self.fetch_one("SELECT user_id FROM users WHERE username = ?", ("admin",))
        if not result:
            password = "psoft123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", password_hash, "ผู้ดูแลระบบ", "admin", 1))
        
        # สร้าง user (พนักงานขาย) ถ้ายังไม่มี
        result = self.fetch_one("SELECT user_id FROM users WHERE username = ?", ("user",))
        if not result:
            password = "user123"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.execute("""
                INSERT INTO users (username, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ("user", password_hash, "พนักงานขาย", "cashier", 1))
        
    def _create_default_categories(self):
        """สร้างหมวดหมู่เริ่มต้น"""
        default_categories = [
            ("อาหารและเครื่องดื่ม", "สินค้าประเภทอาหารและเครื่องดื่ม"),
            ("เครื่องใช้ไฟฟ้า", "อุปกรณ์และเครื่องใช้ไฟฟ้า"),
            ("เสื้อผ้าและแฟชั่น", "เสื้อผ้า รองเท้า กระเป๋า"),
            ("เครื่องสำอาง", "เครื่องสำอางและผลิตภัณฑ์ความงาม"),
            ("ของใช้ในบ้าน", "อุปกรณ์และเครื่องใช้ในบ้าน"),
            ("อื่นๆ", "สินค้าประเภทอื่นๆ"),
        ]
        
        for name, desc in default_categories:
            # ตรวจสอบว่ามีอยู่แล้วหรือไม่
            result = self.fetch_one(
                "SELECT category_id FROM categories WHERE category_name = ?", 
                (name,)
            )
            if not result:
                self.execute(
                    "INSERT INTO categories (category_name, description) VALUES (?, ?)",
                    (name, desc)
                )
                
    def verify_password(self, username, password):
        """ตรวจสอบรหัสผ่าน"""
        user = self.fetch_one(
            "SELECT user_id, password_hash, is_active FROM users WHERE username = ?",
            (username,)
        )
        
        if not user or not user['is_active']:
            return None
            
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return user['user_id']
        return None
        
    def get_user_info(self, user_id):
        """ดึงข้อมูลผู้ใช้"""
        return self.fetch_one(
            """SELECT user_id, username, full_name, role, email, phone, is_active
               FROM users WHERE user_id = ?""",
            (user_id,)
        )
        
    def generate_sale_number(self):
        """สร้างเลขที่ใบเสร็จ"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"SL{today}"
        
        # หาเลขที่ล่าสุดในวันนี้
        result = self.fetch_one(
            """SELECT sale_number FROM sales 
               WHERE sale_number LIKE ? 
               ORDER BY sale_id DESC LIMIT 1""",
            (f"{prefix}%",)
        )
        
        if result:
            last_number = int(result['sale_number'][-4:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}{new_number:04d}"
        
    def generate_return_number(self):
        """สร้างเลขที่ใบคืนสินค้า"""
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"RT{today}"
        
        result = self.fetch_one(
            """SELECT return_number FROM returns 
               WHERE return_number LIKE ? 
               ORDER BY return_id DESC LIMIT 1""",
            (f"{prefix}%",)
        )
        
        if result:
            last_number = int(result['return_number'][-4:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"{prefix}{new_number:04d}"
