# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect(r'data/database.db')
c = conn.cursor()

# ล้างประวัติการขายและการเงิน
tables_to_clear = ['sales', 'sale_items', 'stock_movements', 'login_history']
for t in tables_to_clear:
    try:
        c.execute(f'DELETE FROM {t}')
        print(f'Cleared: {t} ({c.rowcount} rows)')
    except Exception as e:
        print(f'Skip {t}: {e}')

# Reset auto-increment
for t in tables_to_clear:
    try:
        c.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
    except:
        pass

conn.commit()

# ตรวจสอบ
products = c.execute('SELECT COUNT(*) FROM products').fetchone()[0]
sales = c.execute('SELECT COUNT(*) FROM sales').fetchone()[0]
print(f'\nProducts remaining: {products}')
print(f'Sales remaining: {sales}')
conn.close()
print('Done! Sales/financial data cleared, products kept.')
