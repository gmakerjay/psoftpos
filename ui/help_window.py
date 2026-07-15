# -*- coding: utf-8 -*-
"""
หน้าวิธีใช้งาน (Help Guide) — มีสารบัญ, ค้นหาได้, อธิบายทุกฟีเจอร์
"""

import customtkinter as ctk
from config import *


# ===================== ข้อมูลวิธีใช้งาน =====================
HELP_SECTIONS = [
    {
        "id": "overview",
        "icon": "🏠",
        "title": "ภาพรวมโปรแกรม",
        "content": (
            "โปรแกรมขายหน้าร้าน (POS) เป็นระบบจัดการร้านค้าครบวงจร\n"
            "ออกแบบมาเพื่อร้านค้าปลีกทุกขนาด ใช้งานง่ายไม่ต้องเชื่อมต่อเน็ต\n\n"
            "┌─────────────────────────────────────────────────┐\n"
            "│  ✦  ฟีเจอร์ทั้งหมดของโปรแกรม                      │\n"
            "├─────────────────────────────────────────────────┤\n"
            "│  🛒  ขายสินค้าหน้าร้าน — พักบิลได้หลายหน้าขาย      │\n"
            "│  📦  จัดการสินค้า — เพิ่ม/แก้ไข/นำเข้า Excel        │\n"
            "│  📋  ประวัติการขาย — ดูย้อนหลัง/ยกเลิก/พิมพ์ซ้ำ     │\n"
            "│  🔄  คืนสินค้า — คืนเงินลูกค้า + สต็อกกลับ         │\n"
            "│  📦  จัดการสต็อก — แก้ไขตรงๆ / ประวัติเคลื่อนไหว   │\n"
            "│  👥  จัดการผู้ใช้ — กำหนดสิทธิ์ผู้ใช้และสิทธิ์การเข้าถึง │\n"
            "│  📈  รายงาน — ยอดขาย/สินค้าขายดี/สต็อกต่ำ/Export   │\n"
            "│  ⚙️  ตั้งค่า — ร้าน/ภาษี/ใบเสร็จ/เครื่องพิมพ์/สำรอง  │\n"
            "└─────────────────────────────────────────────────┘\n\n"
            "✦ การเข้าใช้งาน\n"
            "  พอเปิดโปรแกรมจะเจอหน้าเข้าสู่ระบบ\n"
            "  ค่าเริ่มต้น → ชื่อผู้ใช้: admin / รหัสผ่าน: admin\n\n"
            "✦ Keyboard Shortcuts ด่วน (กดได้จากทุกหน้า)\n"
            "  • [F1] = ไปหน้าขายสินค้า (POS) + โฟกัสช่องยิงบาร์โค้ดทันที\n"
            "  • [Ctrl+F] = ไปที่ช่องค้นหาของหน้านั้นๆ\n"
            "  • [Ctrl+N] = เพิ่มรายการใหม่\n"
            "  • [Ctrl+R] = รีเฟรชข้อมูลในตาราง"
        )
    },
    {
        "id": "dashboard",
        "icon": "📊",
        "title": "หน้าหลัก (Dashboard)",
        "content": (
            "หน้าแรกหลังเข้าสู่ระบบ แสดงสรุปข้อมูลสำคัญแบบเรียลไทม์\n\n"
            "✦ การ์ดสถิติ (แสดงอัตโนมัติ)\n\n"
            "  💰 ยอดขายวันนี้\n"
            "     แสดงยอดขายรวมและจำนวนรายการที่ขายได้ในวันนี้\n"
            "     คำนวณจากบิลที่ไม่ถูกยกเลิก\n\n"
            "  📅 ยอดขายเดือนนี้\n"
            "     ยอดรวมสะสมตั้งแต่วันที่ 1 ของเดือนถึงวันนี้\n\n"
            "  📦 จำนวนสินค้าทั้งหมด\n"
            "     สินค้าที่ยังเปิดใช้งาน (is_active) ทั้งหมดในระบบ\n\n"
            "  ⚠️ สินค้าใกล้หมด\n"
            "     สินค้าที่สต็อกน้อยกว่า 'สต็อกขั้นต่ำ'\n"
            "     ถ้ามีสินค้าใกล้หมด ให้ไปเติมสต็อกที่หน้า 'จัดการสต็อก' หรือ 'จัดการสินค้า'\n\n"
            "✦ เคล็ดลับ\n"
            "  • เปิดหน้านี้ตอนเช้าเพื่อดูภาพรวมร้านก่อนเริ่มงาน\n"
            "  • ถ้ายอดขายวันนี้เป็น 0 แสดงว่ายังไม่มีการขายหรือยังไม่ login"
        )
    },
    {
        "id": "pos",
        "icon": "🛒",
        "title": "ขายสินค้า (POS)",
        "content": (
            "หน้าจอหลักสำหรับขายสินค้าหน้าร้าน\n"
            "แบ่งเป็น 2 ส่วน: ซ้ายเป็นสินค้า / ขวาเป็นตะกร้า\n\n"
            "━━━━━ ขั้นตอนทั่วไป ━━━━━\n\n"
            "1️⃣  เพิ่มสินค้าลงตะกร้า\n"
            "  • ยิงบาร์โค้ด — สแกนบาร์โค้ดแล้วสินค้าจะเข้าตะกร้าทันที\n"
            "  • ค้นหาด่วน — พิมพ์ชื่อ/บาร์โค้ดในช่องค้นหา (ระบบค้นหาให้ทันที)\n"
            "  • กด F1 — เพื่อโฟกัสและล้างช่องสแกนบาร์โค้ดใหม่ ให้ยิงต่อเนื่องได้ทันที\n"
            "  • คลิกการ์ดสินค้า — กดที่ตัวสินค้าในรายการ\n\n"
            "2️⃣  ปรับจำนวนและราคา\n"
            "  • กดปุ่ม + / - ที่แต่ละรายการในตะกร้า\n"
            "  • หรือเลือกประเภทราคาขายที่แผงขวา (ราคาปลีก, ส่ง, พิเศษ 1, 2)\n\n"
            "3️⃣  ชำระเงินด่วน (ไม่ต้องใช้เมาส์)\n"
            "  • กด [F10] หรือ Enter หรือปุ่ม '💰 ชำระเงิน'\n"
            "  • ใส่จำนวนเงินที่ได้รับจากลูกค้าแล้วกด Enter\n"
            "  • ระบบแสดงเงินทอนอัตโนมัติ และเปิดลิ้นชักเงินสดให้อัตโนมัติ (ถ้าเปิดตั้งค่าไว้)\n"
            "  • กดพิมพ์ใบเสร็จ (Enter) หรือไม่พิมพ์ (Esc)\n\n"
            "━━━━━ ฟีเจอร์พิเศษ ━━━━━\n\n"
            "🔀 หลายหน้าขาย (Multi-Session / พักบิล)\n"
            "  • กด [F9] หรือปุ่ม '+' เพื่อเปิดหน้าขายใหม่แยกอิสระ\n"
            "  • สลับระหว่างหน้าด้วยแท็บด้านบน ทำให้พักบิลลูกค้าเดิมไว้แล้วขายคนใหม่ได้เลย\n\n"
            "🧾 ภาษีมูลค่าเพิ่ม (VAT)\n"
            "  • กด [F8] หรือติ๊กที่ช่อง VAT เพื่อเปิด/ปิดคำนวณภาษีแยกต่างหาก\n\n"
            "🗑️ ล้างตะกร้า\n"
            "  • กด [F11] หรือปุ่ม 'ล้าง' เพื่อล้างข้อมูลสินค้าในตะกร้าปัจจุบัน"
        )
    },
    {
        "id": "products",
        "icon": "📦",
        "title": "จัดการสินค้า",
        "content": (
            "เพิ่ม แก้ไข ลบ และค้นหาสินค้าทั้งหมดในระบบ\n\n"
            "เพิ่มสินค้าใหม่ด่วน (Wizard 6 ขั้นตอน)\n\n"
            "  กด F5 หรือ Ctrl+N หรือปุ่ม 'เพิ่มสินค้า' \n"
            "  ระบบจะพาป้อนข้อมูลทีละขั้นรวดเร็ว ใช้แค่คีย์บอร์ดก็เสร็จ:\n\n"
            "  ขั้น 1  บาร์โค้ด — สแกนบาร์โค้ด หรือกดสร้างอัตโนมัติ/ข้าม\n"
            "  ขั้น 2  ชื่อสินค้า — พิมพ์ชื่อสินค้าแล้วกด Enter\n"
            "  ขั้น 3  ราคาทุน — พิมพ์ราคาทุนแล้วกด Enter\n"
            "  ขั้น 4  ราคาขาย — พิมพ์ราคาขายแล้วกด Enter\n"
            "  ขั้น 5  จำนวนสต็อก — พิมพ์สต็อกเริ่มต้นแล้วกด Enter\n"
            "  ขั้น 6  หมวดหมู่ — กดปุ่มเลือก หรือกดเลข 1 (อุปโภค) หรือ 2 (บริโภค)\n"
            "  (บันทึกสินค้าลงฐานข้อมูลทันทีหลังเสร็จสิ้นขั้นตอน 6)\n\n"
            "แก้ไขสินค้าและสต็อกระหว่างทาง\n\n"
            "  • กดปุ่ม ✏️ (แก้ไข) ท้ายแถวสินค้าที่ต้องการ\n"
            "  • คุณสามารถแก้ไข ชื่อ, ราคา, สต็อกขั้นต่ำ และรูปภาพได้\n"
            "  • สำหรับร้านค้าขนาดเล็ก: **คุณสามารถแก้ไขจำนวนสต็อกสินค้าเดิมได้โดยตรงในหน้านี้เลย**\n"
            "    โดยกรอกจำนวนสต็อกใหม่ลงไป ระบบจะคำนวณส่วนต่างและบันทึกประวัติให้อัตโนมัติ\n\n"
            "นำเข้าจาก Excel (Bulk Import)\n\n"
            "  1. กดปุ่ม 'เทมเพลต' เพื่อโหลดไฟล์ตัวอย่างลงเครื่อง\n"
            "  2. กรอกบาร์โค้ด, ชื่อ, ราคา และสต็อก ลงในไฟล์ Excel ตามรูปแบบเดิม\n"
            "  3. กลับมาที่หน้าโปรแกรม กดปุ่ม 'นำเข้า Excel' และเลือกไฟล์ที่กรอกเสร็จแล้ว"
        )
    },
    {
        "id": "history",
        "icon": "📋",
        "title": "ประวัติการขาย",
        "content": (
            "ดูรายละเอียดการขายย้อนหลัง ยกเลิกบิล และพิมพ์ซ้ำ\n\n"
            "━━━━━ ดูรายละเอียดบิล ━━━━━\n\n"
            "  1. คลิกปุ่ม '📋 ดู' เพื่อแสดงรายการสินค้าและยอดเงินในบิลนั้น\n\n"
            "━━━━━ ยกเลิกบิล (Void) ━━━━━\n\n"
            "  1. คลิกปุ่ม '❌ ยกเลิก' ที่แถวบิลที่ต้องการยกเลิก\n"
            "  2. เมื่อกดยืนยัน ระบบจะ:\n"
            "     • เปลี่ยนสถานะบิลเป็นสีแดง ('ยกเลิก')\n"
            "     • เพิ่มสินค้าทุกชิ้นในบิลนั้นกลับเข้าสต็อกให้อัตโนมัติทันที\n\n"
            "━━━━━ พิมพ์ใบเสร็จซ้ำ ━━━━━\n\n"
            "  1. คลิกปุ่ม '🖨️ พิมพ์' ที่แถวบิลนั้นๆ\n"
            "  2. ระบบจะสั่งพิมพ์ใบเสร็จเดิมออกทางเครื่องพิมพ์อีกครั้ง"
        )
    },
    {
        "id": "returns",
        "icon": "🔄",
        "title": "คืนสินค้า",
        "content": (
            "รับคืนสินค้าจากลูกค้าบางชิ้น — ปรับปรุงสต็อกอัตโนมัติ\n\n"
            "━━━━━ ขั้นตอนการคืนสินค้า ━━━━━\n\n"
            "1️⃣  พิมพ์ค้นหาเลขที่บิลเดิม แล้วกดปุ่มค้นหา\n"
            "2️⃣  กดปุ่ม 'เลือกคืน' ท้ายรายการสินค้าที่ต้องการคืน\n"
            "3️⃣  ปรับจำนวนที่จะคืน (ระบบจะบล็อกไม่ให้คืนเกินจำนวนที่ซื้อจริง)\n"
            "4️⃣  กดปุ่ม '🔄 ดำเนินการคืนสินค้า' ยืนยัน\n\n"
            "✦ ผลลัพธ์หลังยืนยัน\n"
            "  • ระบบจะปรับสต็อกเพิ่มกลับเข้าคลังให้ทันที\n"
            "  • บันทึกประวัติการคืนเงินและจำนวนในระบบอย่างถูกต้อง"
        )
    },
    {
        "id": "stock",
        "icon": "📦",
        "title": "จัดการสต็อก",
        "content": (
            "เพิ่ม ลด และจัดการยอดสต็อกสินค้า พร้อมบันทึกประวัติการเคลื่อนไหว (Audit Trail)\n\n"
            "✦ วิธีการปรับปรุงสต็อก (ทำได้ 2 ช่องทาง):\n\n"
            "1️⃣  แก้ไขด่วน (ใช้ง่ายที่สุดสำหรับผู้สูงอายุ):\n"
            "  • เข้าหน้า 'จัดการสต็อก' > กดปุ่มสีม่วง **✏️ แก้ไขจำนวน** ท้ายสินค้า\n"
            "  • กรอกตัวเลขสต็อกจริงล่าสุดลงไปได้เลย แล้วกดบันทึก\n"
            "  • หรือเข้าไปแก้ไขที่หน้า 'จัดการสินค้า' > กดแก้ไขสินค้า > แก้ไขจำนวนสต็อกได้เช่นกัน\n\n"
            "2️⃣  ปรับสต็อกแบบเพิ่ม/ลดทีละจำนวน:\n"
            "  • กดปุ่ม ➕ หรือ ➖ ท้ายรายการสินค้า\n"
            "  • กรอกจำนวนที่เพิ่ม/ลด และระบุเหตุผล (เช่น รับของเข้า, ตรวจนับจริง, เสียหาย, หมดอายุ)\n\n"
            "━━━━━ ดูประวัติเคลื่อนไหว ━━━━━\n\n"
            "  • คลิกปุ่ม **📋 ประวัติ** (ปุ่มสีฟ้า) ท้ายสินค้า\n"
            "  • ระบบแสดงรายการเคลื่อนไหวทั้งหมด: วันเวลา, ประเภท (ขาย, คืน, แก้ไข), จำนวน และสต็อกก่อน-หลัง"
        )
    },
    {
        "id": "users",
        "icon": "👥",
        "title": "จัดการผู้ใช้",
        "content": (
            "สร้าง แก้ไข ลบ บัญชีผู้ใช้ และกำหนดสิทธิ์การใช้งานระบบ\n"
            "(เมนูนี้เข้าถึงได้เฉพาะ Admin เท่านั้น)\n\n"
            "✦ ระบบสิทธิ์ 3 ระดับ\n"
            "  • Admin: ทำได้ทุกอย่างในโปรแกรม ปลดล็อกตั้งค่าและจัดการผู้ใช้\n"
            "  • Manager: จัดการสินค้า, ปรับสต็อก, ดูรายงานวิเคราะห์ข้อมูลการขาย\n"
            "  • Cashier: ทำรายการขาย POS, ดูประวัติบิล และทำรับคืนสินค้า\n\n"
            "✦ วิธีเพิ่มผู้ใช้ใหม่\n"
            "  กดปุ่ม 'เพิ่มผู้ใช้' > กรอก Username, รหัสผ่าน, ชื่อแสดงตัว และเลือกสิทธิ์ > บันทึก"
        )
    },
    {
        "id": "reports",
        "icon": "📈",
        "title": "รายงานยอดขาย",
        "content": (
            "ดูรายงานสรุปผล ยอดขาย กราฟวิเคราะห์ และส่งออก Excel\n\n"
            "✦ รายงาน 4 หมวดหลัก\n"
            "  • รายงานยอดขาย: ยอดรวม, กำไร, จำนวนบิลรายวัน/รายเดือน\n"
            "  • รายงานจากไฟล์สำรอง: ดึงข้อมูลประวัติยอดขายเก่าๆ ขึ้นมาดูย้อนหลัง\n"
            "  • สินค้าขายดี: เรียงลำดับความนิยมของสินค้าจากมากไปน้อย\n"
            "  • สินค้าสต็อกต่ำ: แสดงเฉพาะรายการที่สินค้าใกล้หมดเพื่อใช้วางแผนสั่งซื้อ\n\n"
            "✦ การส่งออกข้อมูล\n"
            "  กดปุ่ม '📊 Export Excel' เพื่อบันทึกเป็นไฟล์ .xlsx เปิด in Excel ได้ทันที"
        )
    },
    {
        "id": "settings",
        "icon": "⚙️",
        "title": "ตั้งค่าระบบ",
        "content": (
            "ตั้งค่ารายละเอียดทุกจุดของโปรแกรม (มีผลทันที 100%)\n\n"
            "━━━━━ 1. ข้อมูลร้าน ━━━━━\n"
            "  • ตั้งค่าชื่อร้าน, ที่อยู่, โทรศัพท์, เลขประจำตัวผู้เสียภาษี และรูป QR Code สำหรับรับเงินโอน\n"
            "  (รายละเอียดนี้จะไปแสดงบนหัวใบเสร็จและหน้าจอชำระเงิน)\n\n"
            "━━━━━ 2. ภาษีและราคา ━━━━━\n"
            "  • ตั้งค่าอัตราภาษี VAT (เช่น 7%)\n\n"
            "━━━━━ 3. ใบเสร็จ ━━━━━\n"
            "  • ตั้งค่าข้อความท้ายใบเสร็จ, แสดงบาร์โค้ด หรือแสดงชื่อพนักงานบนใบเสร็จ\n\n"
            "━━━━━ 4. เครื่องพิมพ์ ━━━━━\n"
            "  • ประเภทเครื่องพิมพ์: เลือก Windows Printer หรือ Thermal (พิมพ์ตรง)\n"
            "  • ขนาดกระดาษ: เลือก 80mm, 58mm, A4, A5\n"
            "  • มีระบบ Auto-detect ป้องกันกระดาษไหลเปล่ายาวสำหรับขนาด 58mm/80mm\n\n"
            "━━━━━ 5. สำรองข้อมูล ━━━━━\n"
            "  • สำรอง/กู้คืนฐานข้อมูล SQLite เป็นไฟล์ .zip เพื่อป้องกันเครื่องมีปัญหา"
        )
    },
    {
        "id": "faq",
        "icon": "❓",
        "title": "คำถามที่พบบ่อย (FAQ)",
        "content": (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❔ ลิ้นชักเก็บเงินไม่เด้งเปิดตอนชำระเงิน?\n"
            "   ▸ ตรวจสอบสาย RJ11 จากลิ้นชักเสียบเข้าหลังเครื่องพิมพ์สลิปแน่นดีแล้ว\n"
            "   ▸ ไปที่ ตั้งค่า > เครื่องพิมพ์ > ตรวจสอบว่าเลือกเครื่องพิมพ์ที่เปิดใช้งานถูกต้อง\n"
            "   ▸ ตรวจสอบว่าในไฟล์ config ตั้งค่า open_cash_drawer เป็น True\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❔ สต็อกสินค้าไม่ตรง ตรวจเช็คยังไง?\n"
            "   ▸ ไปที่ จัดการสต็อก > กดปุ่ม 📋 ประวัติ ของสินค้าตัวนั้น\n"
            "   ▸ ระบบจะแสดงให้ดูว่าสินค้าหายไปไหน ใครเป็นคนปรับสต็อก หรือขายออกไปช่วงเวลาใดบ้าง\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "❔ วิธีการพิมพ์ใบเสร็จขนาด 58mm ไม่ให้กระดาษฟีดเปล่ายาว?\n"
            "   ▸ โปรแกรมมีระบบคำนวณและปรับขนาดหน้าอัตโนมัติตามเนื้อหาจริงในตัว\n"
            "   ▸ เพียงตรวจสอบใน ตั้งค่า > เครื่องพิมพ์ > เลือกขนาดกระดาษเป็น 58mm หรือ 80mm ให้ตรงกับเครื่องพิมพ์ของคุณ"
        )
    },
]


class HelpGuideFrame(ctk.CTkFrame):
    """Frame วิธีใช้งาน — มีสารบัญ + ค้นหา + เนื้อหาครบทุกฟีเจอร์"""

    def __init__(self, parent, user_id=None):
        super().__init__(parent, fg_color=COLORS["light"])
        self.sections = HELP_SECTIONS
        self.section_widgets = {}  # เก็บ reference widget ของแต่ละ section
        self.toc_buttons = {}
        self.create_widgets()

    def create_widgets(self):
        """สร้าง UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        title = ctk.CTkLabel(
            header,
            text="วิธีใช้งานโปรแกรม",
            font=("Sarabun", 26, "bold"),
            text_color=COLORS["primary"]
        )
        title.pack(side="left")

        # ช่องค้นหา
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="right")

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 ค้นหาหัวข้อ...",
            font=FONTS["body"],
            width=300,
            height=40
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_sections())

        clear_btn = ctk.CTkButton(
            search_frame,
            text="✕",
            width=40, height=40,
            font=("Arial", 16),
            fg_color=COLORS["text_light"],
            command=self.clear_search
        )
        clear_btn.pack(side="left")

        # เนื้อหาหลัก: 2 คอลัมน์
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ===== คอลัมน์ซ้าย: สารบัญ =====
        toc_frame = ctk.CTkFrame(main, width=220, fg_color="white", corner_radius=10)
        toc_frame.pack(side="left", fill="y", padx=(0, 10))
        toc_frame.pack_propagate(False)

        toc_title = ctk.CTkLabel(
            toc_frame,
            text="สารบัญ",
            font=("Sarabun", 18, "bold"),
            text_color=COLORS["primary"]
        )
        toc_title.pack(padx=15, pady=(15, 10), anchor="w")

        # สร้างปุ่มสารบัญ
        self.toc_scroll = ctk.CTkScrollableFrame(toc_frame, fg_color="transparent")
        self.toc_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        for section in self.sections:
            btn = ctk.CTkButton(
                self.toc_scroll,
                text=section['title'],
                font=("Sarabun", 15, "bold"),
                height=42,
                anchor="w",
                fg_color="transparent",
                text_color=COLORS["text_dark"],
                hover_color=COLORS["light"],
                command=lambda sid=section["id"]: self.scroll_to_section(sid)
            )
            btn.pack(fill="x", padx=5, pady=2)
            self.toc_buttons[section["id"]] = btn

        # ===== คอลัมน์ขวา: เนื้อหา =====
        self.content_scroll = ctk.CTkScrollableFrame(
            main, fg_color="white", corner_radius=10
        )
        self.content_scroll.pack(side="right", fill="both", expand=True)

        self.build_content()

    def build_content(self):
        """สร้างเนื้อหาทุก section"""
        for widget in self.content_scroll.winfo_children():
            widget.destroy()
        self.section_widgets.clear()

        for section in self.sections:
            self._create_section_widget(section, self.content_scroll)

    def _create_section_widget(self, section, parent):
        """สร้าง widget สำหรับ section เดียว"""
        section_frame = ctk.CTkFrame(
            parent, fg_color="white", corner_radius=12
        )
        section_frame.pack(fill="x", padx=15, pady=10)

        # หัวข้อ — พื้นหลังสีน้ำเงิน ตัวอักษรขาว ใหญ่ หนา
        header_bg = ctk.CTkFrame(
            section_frame, fg_color=COLORS["primary"], corner_radius=10
        )
        header_bg.pack(fill="x", padx=0, pady=0)

        header = ctk.CTkLabel(
            header_bg,
            text=section['title'],
            font=("Sarabun", 26, "bold"),
            text_color="white",
            anchor="w",
        )
        header.pack(fill="x", padx=22, pady=16)

        # เนื้อหา — ฟอนต์ใหญ่ขึ้น อ่านง่าย
        body = ctk.CTkLabel(
            section_frame,
            text=section["content"],
            font=("Sarabun", 16),
            text_color=COLORS["text_dark"],
            anchor="nw",
            justify="left",
            wraplength=720,
        )
        body.pack(fill="x", padx=25, pady=(14, 20))

        self.section_widgets[section["id"]] = section_frame

    def scroll_to_section(self, section_id):
        """เลื่อนไปยัง section ที่เลือก"""
        widget = self.section_widgets.get(section_id)
        if widget:
            # Highlight ปุ่มสารบัญ
            for sid, btn in self.toc_buttons.items():
                if sid == section_id:
                    btn.configure(fg_color=COLORS["primary"], text_color="white")
                else:
                    btn.configure(fg_color="transparent", text_color=COLORS["text_dark"])

            # เลื่อน content scroll ให้ widget อยู่ด้านบน
            self.content_scroll.update_idletasks()
            try:
                widget_y = widget.winfo_y()
                total_height = self.content_scroll._parent_frame.winfo_height()
                if total_height > 0:
                    fraction = widget_y / max(total_height, 1)
                    self.content_scroll._parent_canvas.yview_moveto(max(0, min(fraction, 1.0)))
            except Exception:
                pass

    def filter_sections(self):
        """กรองเนื้อหาตามคำค้นหา"""
        query = self.search_entry.get().strip().lower()

        if not query:
            self.build_content()
            for btn in self.toc_buttons.values():
                btn.pack(fill="x", padx=5, pady=2)
            return

        # ล้างเนื้อหาเดิม
        for widget in self.content_scroll.winfo_children():
            widget.destroy()
        self.section_widgets.clear()

        found = False
        for section in self.sections:
            match = (
                query in section["title"].lower()
                or query in section["content"].lower()
            )

            btn = self.toc_buttons.get(section["id"])
            if btn:
                if match:
                    btn.pack(fill="x", padx=5, pady=2)
                else:
                    btn.pack_forget()

            if match:
                found = True
                self._create_section_widget(section, self.content_scroll)

        if not found:
            no_result = ctk.CTkLabel(
                self.content_scroll,
                text=f"ไม่พบหัวข้อที่ค้นหา: '{query}'",
                font=FONTS["body"],
                text_color=COLORS["text_light"]
            )
            no_result.pack(pady=50)

    def clear_search(self):
        """ล้างค้นหาและแสดงทั้งหมด"""
        self.search_entry.delete(0, "end")
        self.filter_sections()
