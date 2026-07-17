# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File สำหรับโปรแกรมขายหน้าร้าน - เวอร์ชันทดลองใช้ 3 วัน
"""

import os
import customtkinter
from pathlib import Path

block_cipher = None

# กำหนด path หลัก
base_path = Path(SPECPATH)

# หา path ของ customtkinter
ctk_path = Path(os.path.dirname(customtkinter.__file__))

# รวบรวม data files ที่จำเป็น
datas = [
    ('icon.ico', '.'),  # ไอคอนโปรแกรม
    ('config.py', '.'),
    ('performance_config.py', '.'),
    ('FC Sara Samkan [Non-commercial] Bold.ttf', '.'), # ฟอนต์ภาษาไทย
    ('assets', 'assets'), # รวมโฟลเดอร์ assets
    (str(ctk_path / 'assets'), 'customtkinter/assets'), # CustomTkinter assets
]

# รวบรวม hidden imports ที่ PyInstaller อาจพลาด
hiddenimports = [
    'customtkinter',
    'PIL',
    'PIL._tkinter_finder',
    'barcode',
    'barcode.writer',
    'qrcode',
    'openpyxl',
    'pandas',
    'reportlab',
    'reportlab.graphics.barcode',
    'reportlab.graphics.barcode.code128',
    'reportlab.graphics.barcode.common',
    'matplotlib',
    'numpy',
    'tkcalendar',
    'serial',
    'escpos',
    'bcrypt',
    'cryptography',
    'win32print',
    'win32ui',
    'win32api',
    'win32con',
    'pywintypes',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    '_tkinter',
    'sqlite3',
    'datetime',
    'json',
    'csv',
    'base64',
    'hashlib',
    'uuid',
    'platform',
    'socket',
    'ui',
    'ui.login_window',
    'ui.main_window',
    'ui.pos_window',
    'ui.product_window',
    'ui.stock_window',
    'ui.reports_window',
    'ui.users_window',
    'ui.settings_window',
    'ui.history_window',
    'ui.returns_window',
    'ui.parked_window',
    'ui.brand_window',
    'ui.vendor_window',
    'ui.customer_display',
    'ui.activation_window',
    'ui.help_window',
    'database',
    'database.db_manager',
    'utils',
    'utils.logger',
    'utils.image_utils',
    'utils.barcode_utils',
    'utils.excel_utils',
    'utils.pdf_utils',
    'utils.printer_utils',
    'utils.backup_utils',
    'utils.license_system',
    'utils.license_system_trial_3days',
    'utils.shop_status',
    'utils.tax_invoice',
    'utils.delivery_note',
    'utils.input_utils',
]

binaries = []

a = Analysis(
    ['main_trial_3days.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'license_manager',
        'license_generator',
        'torch',
        'torchvision',
        'torchaudio',
        'tensorboard',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StorePOS_3DayTrial',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StorePOS_3DayTrial',
)
