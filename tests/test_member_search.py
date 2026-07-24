# -*- coding: utf-8 -*-
"""
Test Member & Phone Number Search Logic
"""
import sys
import os

# Set root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def test_member_search():
    db = DatabaseManager()
    db.connect()
    
    # 1. Fetch all members first
    all_members = db.fetch_all("SELECT member_id, name, phone, privilege, points FROM members")
    print(f"[TEST] Total Members in DB: {len(all_members)}")
    for m in all_members:
        print(f"  - ID: {m['member_id']} | Name: {m['name']} | Phone: {m['phone']}")
        
    assert len(all_members) > 0, "Should have members in DB"
    
    # 2. Test search by name
    test_member = all_members[0]
    name_query = test_member['name'][:3]
    members_by_name = db.fetch_all(
        """SELECT member_id, name, phone 
           FROM members 
           WHERE LOWER(name) LIKE ? 
              OR REPLACE(phone, '-', '') LIKE ? 
              OR phone LIKE ? 
           ORDER BY name""",
        (f"%{name_query.lower()}%", f"%{name_query}%", f"%{name_query}%")
    )
    print(f"\n[TEST] Search by name query '{name_query}': Found {len(members_by_name)} match(es)")
    assert len(members_by_name) >= 1, "Should find member by name"
    
    # 3. Test search by phone (raw digits & formatted)
    if test_member['phone']:
        phone = test_member['phone']
        raw_phone = phone.replace("-", "").strip()
        formatted_phone = f"{raw_phone[:3]}-{raw_phone[3:6]}-{raw_phone[6:]}" if len(raw_phone) >= 10 else raw_phone
        
        # Test raw search
        res_raw = db.fetch_all(
            """SELECT member_id, name, phone 
               FROM members 
               WHERE LOWER(name) LIKE ? 
                  OR REPLACE(phone, '-', '') LIKE ? 
                  OR phone LIKE ? 
               ORDER BY name""",
            (f"%{raw_phone.lower()}%", f"%{raw_phone}%", f"%{raw_phone}%")
        )
        print(f"[TEST] Search by raw phone '{raw_phone}': Found {len(res_raw)} match(es)")
        assert len(res_raw) >= 1, "Should find member by raw phone"
        
        # Test formatted search
        res_fmt = db.fetch_all(
            """SELECT member_id, name, phone 
               FROM members 
               WHERE LOWER(name) LIKE ? 
                  OR REPLACE(phone, '-', '') LIKE ? 
                  OR phone LIKE ? 
               ORDER BY name""",
            (f"%{formatted_phone.lower()}%", f"%{raw_phone}%", f"%{formatted_phone}%")
        )
        print(f"[TEST] Search by formatted phone '{formatted_phone}': Found {len(res_fmt)} match(es)")
        assert len(res_fmt) >= 1, "Should find member by formatted phone"

    db.disconnect()
    print("\n✅ [ALL MEMBER SEARCH TESTS PASSED 100%]")

if __name__ == "__main__":
    test_member_search()
