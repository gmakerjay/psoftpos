# -*- coding: utf-8 -*-
"""
Test script for translate_thai_barcode function
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.input_utils import translate_thai_barcode

def test_translation():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== Testing translate_thai_barcode ===")
    
    # 1. Test case: Thai Kedmanee input representing barcode "8850999010010"
    thai_scanned = "คคถจตตตจๅจจๅจ"
    expected = "8850999010010"
    actual = translate_thai_barcode(thai_scanned)
    print(f"Thai Layout Scan: {thai_scanned}")
    print(f"Translated:      {actual}")
    print(f"Expected:        {expected}")
    assert actual == expected, "Barcode translation failed!"
    print("[PASS] Test case 1: Scanned barcode successfully translated to digits.")
    
    # 2. Test case: Normal Thai word search (should not be translated)
    thai_search = "น้ำดื่ม ตราสิงห์"
    actual2 = translate_thai_barcode(thai_search)
    print(f"Thai Search:     {thai_search}")
    print(f"Translated:      {actual2}")
    assert actual2 == thai_search, "Normal Thai search text was incorrectly translated!"
    print("[PASS] Test case 2: Normal Thai word search left untouched.")
    
    # 3. Test case: Mixed / Short input (should not be translated)
    short_input = "ค"
    actual3 = translate_thai_barcode(short_input)
    print(f"Short Input:     {short_input}")
    print(f"Translated:      {actual3}")
    assert actual3 == short_input, "Short text was incorrectly translated!"
    print("[PASS] Test case 3: Short input left untouched.")

    print("\n=> ALL TRANSLATION TESTS PASSED!")

if __name__ == "__main__":
    test_translation()
