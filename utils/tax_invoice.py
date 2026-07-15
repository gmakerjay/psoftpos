# -*- coding: utf-8 -*-
"""
Tax Invoice Generator - สร้างใบกำกับภาษีตามมาตรฐาน e-Tax Invoice
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import qrcode
from io import BytesIO


class TaxInvoiceGenerator:
    """สร้างใบกำกับภาษี (Tax Invoice) แบบ e-Tax"""
    
    def __init__(self, shop_info):
        """
        shop_info = {
            'name': 'ชื่อร้าน',
            'tax_id': 'เลขประจำตัวผู้เสียภาษี 13 หลัก',
            'address': 'ที่อยู่',
            'tel': 'เบอร์โทร',
            'branch': 'สาขา (สำนักงานใหญ่/สาขาที่ xxxx)'
        }
        """
        self.shop_info = shop_info
        
        # สร้างโฟลเดอร์เก็บ PDF
        os.makedirs("data/tax_invoices", exist_ok=True)
        os.makedirs("temp", exist_ok=True)
    
    def generate_invoice_number(self):
        """สร้างเลขที่ใบกำกับภาษี: INV-YYYYMMDD-XXXX"""
        today = datetime.now().strftime("%Y%m%d")
        
        # นับจำนวนไฟล์ในวันนี้
        files = os.listdir("data/tax_invoices")
        today_files = [f for f in files if f.startswith(f"INV-{today}")]
        sequence = len(today_files) + 1
        
        return f"INV-{today}-{sequence:04d}"
    
    def generate_qr_code(self, invoice_data):
        """สร้าง QR Code สำหรับ e-Tax Invoice"""
        # ข้อมูลตาม e-Tax Invoice Standard
        qr_data = f"""
TAX_INVOICE
เลขที่: {invoice_data['invoice_no']}
วันที่: {invoice_data['date']}
ผู้ขาย: {self.shop_info['name']}
เลขประจำตัวผู้เสียภาษี: {self.shop_info['tax_id']}
ผู้ซื้อ: {invoice_data.get('customer_name', 'ลูกค้าทั่วไป')}
ยอดรวม: {invoice_data['total']:,.2f} บาท
ภาษี 7%: {invoice_data['vat']:,.2f} บาท
""".strip()
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # บันทึกไปยัง BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # บันทึกไฟล์ชั่วคราว
        qr_path = f"temp/qr_{invoice_data['invoice_no']}.png"
        with open(qr_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return qr_path
    
    def create_invoice(self, sale_data):
        """
        สร้างใบกำกับภาษี
        
        sale_data = {
            'sale_id': 1,
            'sale_date': '2024-12-05 14:30:00',
            'customer_name': 'บริษัท XXX จำกัด',
            'customer_tax_id': '1234567890123',
            'customer_address': 'ที่อยู่ลูกค้า',
            'items': [
                {
                    'product_name': 'สินค้า A',
                    'quantity': 2,
                    'price': 100.00,
                    'amount': 200.00
                }
            ],
            'subtotal': 200.00,  # ราคาก่อน VAT
            'vat': 14.00,        # VAT 7%
            'total': 214.00      # ราคารวม VAT
        }
        """
        invoice_no = self.generate_invoice_number()
        invoice_date = datetime.strptime(sale_data['sale_date'], "%Y-%m-%d %H:%M:%S")
        
        # ข้อมูลใบกำกับภาษี
        invoice_data = {
            'invoice_no': invoice_no,
            'date': invoice_date.strftime("%d/%m/%Y"),
            'time': invoice_date.strftime("%H:%M:%S"),
            'customer_name': sale_data.get('customer_name', 'ลูกค้าทั่วไป'),
            'customer_tax_id': sale_data.get('customer_tax_id', '-'),
            'customer_address': sale_data.get('customer_address', '-'),
            'items': sale_data['items'],
            'subtotal': sale_data['subtotal'],
            'vat': sale_data['vat'],
            'total': sale_data['total']
        }
        
        # สร้าง PDF
        pdf_path = f"data/tax_invoices/{invoice_no}.pdf"
        doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                                leftMargin=15*mm, rightMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)
        
        story = []
        
        # === Header ===
        story.append(Spacer(1, 10*mm))
        
        # ชื่อเอกสาร
        title_style = ParagraphStyle(
            'Title',
            fontSize=20,
            alignment=TA_CENTER,
            fontName='THSarabunNew-Bold',
            textColor=colors.HexColor('#1565C0')
        )
        story.append(Paragraph("<b>ใบกำกับภาษี / Tax Invoice</b>", title_style))
        story.append(Spacer(1, 3*mm))
        
        # เลขที่ใบกำกับภาษี
        invoice_no_style = ParagraphStyle(
            'InvoiceNo',
            fontSize=14,
            alignment=TA_CENTER,
            fontName='THSarabunNew'
        )
        story.append(Paragraph(f"เลขที่ / No.: <b>{invoice_no}</b>", invoice_no_style))
        story.append(Spacer(1, 5*mm))
        
        # === ข้อมูลผู้ขาย-ผู้ซื้อ ===
        info_data = [
            # ผู้ขาย
            [
                Paragraph("<b>ผู้ขาย / Seller:</b>", ParagraphStyle('Normal', fontSize=12, fontName='THSarabunNew-Bold')),
                Paragraph("<b>ผู้ซื้อ / Buyer:</b>", ParagraphStyle('Normal', fontSize=12, fontName='THSarabunNew-Bold'))
            ],
            [
                Paragraph(f"{self.shop_info['name']}", ParagraphStyle('Normal', fontSize=11, fontName='THSarabunNew')),
                Paragraph(f"{invoice_data['customer_name']}", ParagraphStyle('Normal', fontSize=11, fontName='THSarabunNew'))
            ],
            [
                Paragraph(f"{self.shop_info['address']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew')),
                Paragraph(f"{invoice_data['customer_address']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew'))
            ],
            [
                Paragraph(f"เลขประจำตัวผู้เสียภาษี: <b>{self.shop_info['tax_id']}</b>", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew')),
                Paragraph(f"เลขประจำตัวผู้เสียภาษี: <b>{invoice_data['customer_tax_id']}</b>", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew'))
            ],
            [
                Paragraph(f"โทร: {self.shop_info['tel']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew')),
                Paragraph(f"วันที่: <b>{invoice_data['date']} {invoice_data['time']}</b>", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew'))
            ],
            [
                Paragraph(f"สาขา: {self.shop_info['branch']}", ParagraphStyle('Normal', fontSize=10, fontName='THSarabunNew')),
                ""
            ]
        ]
        
        info_table = Table(info_data, colWidths=[90*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 5*mm))
        
        # === ตารางสินค้า ===
        items_data = [
            ['ลำดับ', 'รายการ', 'จำนวน', 'ราคา/หน่วย', 'จำนวนเงิน']
        ]
        
        for i, item in enumerate(invoice_data['items'], 1):
            items_data.append([
                str(i),
                item['product_name'],
                f"{item['quantity']:.2f}",
                f"{item['price']:,.2f}",
                f"{item['amount']:,.2f}"
            ])
        
        # เว้นบรรทัดว่าง
        for _ in range(max(0, 10 - len(invoice_data['items']))):
            items_data.append(['', '', '', '', ''])
        
        items_table = Table(items_data, colWidths=[15*mm, 95*mm, 20*mm, 25*mm, 25*mm])
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'THSarabunNew-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'THSarabunNew'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # ลำดับ
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # รายการ
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # ตัวเลข
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 3*mm))
        
        # === สรุปยอด ===
        summary_data = [
            ['รวมเป็นเงิน (Subtotal)', f"{invoice_data['subtotal']:,.2f} บาท"],
            ['ภาษีมูลค่าเพิ่ม 7% (VAT 7%)', f"{invoice_data['vat']:,.2f} บาท"],
            ['<b>จำนวนเงินทั้งสิ้น (Total)</b>', f"<b>{invoice_data['total']:,.2f} บาท</b>"]
        ]
        
        summary_table = Table(summary_data, colWidths=[155*mm, 25*mm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'THSarabunNew'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.grey),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 8*mm))
        
        # === QR Code + ลายเซ็น ===
        qr_path = self.generate_qr_code(invoice_data)
        
        footer_data = [
            [
                Image(qr_path, width=40*mm, height=40*mm),
                Paragraph("<b>ผู้จัดทำ</b><br/><br/><br/>_______________________<br/>วันที่: _____/_____/_____",
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabunNew')),
                Paragraph("<b>ผู้อนุมัติ</b><br/><br/><br/>_______________________<br/>วันที่: _____/_____/_____",
                          ParagraphStyle('Center', fontSize=10, alignment=TA_CENTER, fontName='THSarabunNew'))
            ]
        ]
        
        footer_table = Table(footer_data, colWidths=[60*mm, 60*mm, 60*mm])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(footer_table)
        
        # สร้าง PDF
        doc.build(story)
        
        # ลบ QR Code ชั่วคราว
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        return pdf_path, invoice_no


# ทดสอบ
if __name__ == "__main__":
    # ข้อมูลร้าน
    shop_info = {
        'name': 'บริษัท ตัวอย่าง จำกัด',
        'tax_id': '0123456789012',
        'address': '123 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพฯ 10110',
        'tel': '02-123-4567',
        'branch': 'สำนักงานใหญ่'
    }
    
    # ข้อมูลการขาย
    sale_data = {
        'sale_id': 1,
        'sale_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'customer_name': 'บริษัท ลูกค้า จำกัด',
        'customer_tax_id': '9876543210123',
        'customer_address': '456 ถนนเพชรบุรี แขวงมักกะสัน เขตราชเทวี กรุงเทพฯ 10400',
        'items': [
            {
                'product_name': 'สินค้า A',
                'quantity': 2,
                'price': 100.00,
                'amount': 200.00
            },
            {
                'product_name': 'สินค้า B',
                'quantity': 1,
                'price': 350.50,
                'amount': 350.50
            },
            {
                'product_name': 'สินค้า C',
                'quantity': 3,
                'price': 50.00,
                'amount': 150.00
            }
        ],
        'subtotal': 700.50,
        'vat': 49.04,
        'total': 749.54
    }
    
    # สร้างใบกำกับภาษี
    generator = TaxInvoiceGenerator(shop_info)
    
    try:
        pdf_path, invoice_no = generator.create_invoice(sale_data)
        print(f"✅ สร้างใบกำกับภาษีสำเร็จ!")
        print(f"📄 เลขที่: {invoice_no}")
        print(f"💾 ไฟล์: {pdf_path}")
        
        # เปิดไฟล์
        os.startfile(pdf_path)
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
