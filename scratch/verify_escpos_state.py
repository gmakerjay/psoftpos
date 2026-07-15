# -*- coding: utf-8 -*-
"""
ESC/POS Byte Parser & Simulator (Version 2)
พิสูจน์การทำงานการถอดรหัสของเครื่องพิมพ์ Thermal และรหัสอักษรเกาหลี
"""
import sys

# ข้อมูลดิบจำลองของภาษาไทยคำว่า "น้ำมันพืช" ในรหัส CP874 (Thai Windows)
# น = 0xb9, ำ = 0xd5, ้ = 0xe9, ม = 0xb8, ั = 0xd1, น = 0xb9, พ = 0xc5, ื = 0xd7, ช = 0xaa
thai_raw_bytes = bytes([0xb9, 0xd5, 0xe9, 0xb8, 0xd1, 0xb9, 0xc5, 0xd7, 0xaa])

def simulate_printer(job_bytes):
    state = {
        "double_byte_mode": False,
        "code_page": 0,
        "output_chars": []
    }
    
    i = 0
    while i < len(job_bytes):
        # 1. เช็คคำสั่ง ESC (0x1B)
        if job_bytes[i] == 0x1B:
            if i + 1 < len(job_bytes):
                cmd = job_bytes[i+1]
                if cmd == ord('@'):
                    state["double_byte_mode"] = False
                    state["code_page"] = 0
                    i += 2
                    continue
                elif cmd == ord('t'):
                    if i + 2 < len(job_bytes):
                        state["code_page"] = job_bytes[i+2]
                        i += 3
                        continue
            i += 1
        # 2. เช็คคำสั่ง FS (0x1C)
        elif job_bytes[i] == 0x1C:
            if i + 1 < len(job_bytes):
                cmd = job_bytes[i+1]
                if cmd == ord('.'):
                    state["double_byte_mode"] = False
                    i += 2
                    continue
                elif cmd == ord('&'):
                    state["double_byte_mode"] = True
                    i += 2
                    continue
            i += 1
        # 3. จัดการข้อมูลตัวอักษร
        else:
            byte_val = job_bytes[i]
            if state["double_byte_mode"]:
                if i + 1 < len(job_bytes):
                    next_byte = job_bytes[i+1]
                    double_byte = bytes([byte_val, next_byte])
                    # ในเอเชียตะวันออก เครื่องพิมพ์มักจะถูกเซ็ตโรงงานไว้เป็นรหัส GBK (จีน) หรือ EUC-KR (เกาหลี)
                    # ลองแปลงไบต์คู่นี้เป็นเกาหลี (EUC-KR) และจีน (GBK)
                    char_kr = ""
                    try:
                        char_kr = double_byte.decode('euc-kr')
                    except Exception:
                        char_kr = "?"
                        
                    char_cn = ""
                    try:
                        char_cn = double_byte.decode('gbk')
                    except Exception:
                        char_cn = "?"
                        
                    state["output_chars"].append({
                        "bytes": f"{byte_val:02X} {next_byte:02X}",
                        "euc_kr": char_kr,
                        "gbk": char_cn
                    })
                    i += 2
                else:
                    state["output_chars"].append({
                        "bytes": f"{byte_val:02X}",
                        "euc_kr": chr(byte_val),
                        "gbk": chr(byte_val)
                    })
                    i += 1
            else:
                if state["code_page"] == 26: # CP874 Thai
                    try:
                        char = bytes([byte_val]).decode('cp874')
                    except Exception:
                        char = "?"
                else:
                    char = chr(byte_val)
                state["output_chars"].append(char)
                i += 1
                
    return state

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    
    # คำสั่งเคสที่ 1 (มีคำสั่ง FS &)
    case1_bytes = bytes([
        0x1B, ord('@'),      # ESC @
        0x1C, ord('.'),      # FS .
        0x1C, ord('&'),      # FS & (เปิดใช้โหมดสองไบต์)
        0x1B, ord('t'), 26,  # ESC t 26
    ]) + thai_raw_bytes
    
    # คำสั่งเคสที่ 2 (ไม่มี FS & และมี FS . คอยปิดโหมดสองไบต์)
    case2_bytes = bytes([
        0x1B, ord('@'),      # ESC @
        0x1C, ord('.'),      # FS . (ปิดโหมดสองไบต์)
        0x1B, ord('t'), 26,  # ESC t 26
    ]) + thai_raw_bytes
    
    result1 = simulate_printer(case1_bytes)
    result2 = simulate_printer(case2_bytes)
    
    print("=" * 70)
    print("  พิสูจน์ทางวิทยาศาสตร์คอมพิวเตอร์: ทำไมพิมพ์ภาษาไทยแล้วออกเป็นเกาหลี/จีน?")
    print("=" * 70)
    print("ข้อความที่ส่ง: 'น้ำมันพืช'")
    print(f"รหัสรหัสไบต์ดิบ (CP874): {[f'{b:02X}' for b in thai_raw_bytes]}")
    print("-" * 70)
    print("กรณีที่ 1: ส่งคำสั่ง 'FS &' (เปิดโหมดตัวอักษร 2 ไบต์ค้างไว้)")
    print("เครื่องพิมพ์จะทำการจับคู่ไบต์ทีละ 2 ตัวแล้วแปลงผลลัพธ์ ดังนี้:")
    print("  คู่ไบต์ที่ส่ง    ->  หากเครื่องเป็นโหมดเกาหลี (EUC-KR)  /  หากเป็นโหมดจีน (GBK)")
    for item in result1['output_chars']:
        if isinstance(item, dict):
            print(f"  {item['bytes']}          ->  '{item['euc_kr']}'                           /  '{item['gbk']}'")
        else:
            print(f"  {item} (เศษตัวสุดท้าย)")
            
    print("-" * 70)
    print("กรณีที่ 2: เอา 'FS &' ออก (บังคับปิดโหมด 2 ไบต์ด้วย 'FS .' และใช้ Single-Byte CP874)")
    print("เครื่องพิมพ์จะมองไบต์แยกทีละ 1 ตัวอย่างถูกต้อง:")
    print(f"  ผลลัพธ์บนกระดาษ: '{''.join(result2['output_chars'])}'")
    print("=" * 70)
